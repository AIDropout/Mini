"""
Main entry point for the fastapi application.
Sets up the application with its routes, middleware, and event handlers.
"""

import asyncio
import subprocess
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pyngrok import ngrok

from config.config import config
from config.container import container
from mini.api import router as api_router
from mini.core.logger import get_logger
from mini.messaging.bird.bird import BirdMessaging
from mini.messaging.telegram.telegram import TelegramManager
from mini.utils.utils import stop_existing_processes

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI):
    """Life cycle of FastAPI server."""

    redis_manager = container.get_redis_manager()
    redis_manager.initialize()
    apscheduler = container.get_apscheduler()
    apscheduler.initialize()

    if config.is_local():
        # redis_manager.flush_all()
        subprocess.Popen(
            [
                "celery",
                "-A",
                "mini.server.celery.celery",
                "worker",
                "-n",
                "worker1@%h",
                "--loglevel=ERROR",
            ]
        )

    yield

    redis_manager.close()
    apscheduler.close()
    subprocess.run(["pkill", "-f", "celery"], check=False)
    ngrok.kill()


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Middleware to log HTTP requests and responses, with special handling for Stripe requests."""
    is_stripe_request = "Stripe" in request.headers.get("User-Agent", "")

    # Log the basic request info
    logger.info("%s %s", request.method, request.url)

    if not is_stripe_request:
        # Log additional request details if not from Stripe
        logger.info("Headers: %s", request.headers)
        body = await request.body()
        logger.info("Body: %s", body.decode())

    response = await call_next(request)

    return response


async def configure_local_webhooks(local_url: str) -> None:
    """Sets up an Ngrok public URL, and directs received Bird/Telegram messages to the URL"""

    ngrok_connection = ngrok.connect(addr=local_url, proto="http")
    logger.info("Ngrok public URL: %s", ngrok_connection.public_url)
    if ngrok_connection.public_url is None:
        raise ValueError("Ngrok Public URL is None")
    config.NGROK_CONFIG.set_url(ngrok_connection.public_url)

    _telegram = TelegramManager()
    _bird = BirdMessaging()

    _bird.set_sender(config.BIRD_DEV_CHANNEL_ID)

    await asyncio.gather(
        # _telegram.register_webhook(webhook),
        _bird.register_webhook(
            event="sms.inbound",
            webhook_url=f"{ngrok_connection.public_url}/webhooks/bird",
        ),
    )

    logger.info("Ngrok and webhooks successfully set up!")


def run_app():
    """
    Main entry point for starting the FastAPI server.
    This function configures webhooks for the server and starts the FastAPI server.
    """
    local_url = "127.0.0.1"
    port = 8000
    use_gunicorn = False

    asyncio.run(configure_local_webhooks(f"{local_url}:{port}"))

    # Stops all existing servers
    stop_existing_processes(port)

    if use_gunicorn:
        # Start Gunicorn server
        gunicorn_command = [
            "gunicorn",
            "-w",
            "4",
            "-k",
            "uvicorn.workers.UvicornWorker",
            "main:app",
            "--bind",
            f"{local_url}:{port}",
        ]
        subprocess.Popen(gunicorn_command)
    else:
        # Start Uvicorn server
        uvicorn.run("main:app", host=local_url, port=port, reload=True)


if __name__ == "__main__":
    run_app()
