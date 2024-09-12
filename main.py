import asyncio
import subprocess
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pyngrok import ngrok

from config.config import config
from mini.api import router as api_router
from mini.core.logger import get_logger
from mini.server.redis import RedisManager
from mini.utils.utils import configure_local_webhooks, stop_existing_processes

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Life cycle of FastAPI server"""
    redis_manager = RedisManager()
    redis_manager.initialize()

    if config.ENVIRONMENT == "local":
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
            + (["--beat"] if config.ENABLE_CELERY_BEAT else [])
        )

    yield

    subprocess.run(["pkill", "-f", "celery"])
    ngrok.kill()
    redis_manager.close()


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
    logger.info(f"{request.method} {request.url}")

    if not is_stripe_request:
        # Log additional request details if not from Stripe
        logger.info(f"Headers: {request.headers}")
        body = await request.body()
        logger.info(f"Body: {body.decode()}")

    response = await call_next(request)

    return response


def run_app():
    LOCAL_URL = "127.0.0.1"
    PORT = 8000
    USE_GUNICORN = False

    asyncio.run(configure_local_webhooks(f"{LOCAL_URL}:{PORT}"))

    # Stops all existing servers
    stop_existing_processes(PORT)

    if USE_GUNICORN:
        # Start Gunicorn server
        gunicorn_command = [
            "gunicorn",
            "-w",
            "4",
            "-k",
            "uvicorn.workers.UvicornWorker",
            "main:app",
            "--bind",
            f"{LOCAL_URL}:{PORT}",
        ]
        subprocess.Popen(gunicorn_command)
    else:
        # Start Uvicorn server
        import uvicorn

        uvicorn.run("main:app", host=LOCAL_URL, port=PORT, reload=True)


if __name__ == "__main__":
    run_app()
