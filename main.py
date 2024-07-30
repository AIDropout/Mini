import asyncio
import os
import subprocess
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from pyngrok import ngrok
from starlette.middleware.base import BaseHTTPMiddleware
from config.config import config
from zootopia.platform.telegram.telegram import Telegram
from zootopia.platform.sms.bird import BirdSMSProvider
from zootopia.core.logger import logger
from zootopia.core.routers import signup_router, message_router, cron_router
from zootopia.server.redis import redis_manager


LOCAL_URL = "127.0.0.1"
PORT = 8000


def stop_existing_servers():
    try:
        pids = subprocess.check_output(["lsof", "-t", f"-i:{PORT}"]).split()
        for pid in pids:
            logger.info(f"Killing process {pid.decode()} using port {PORT}")
            subprocess.run(["kill", "-9", pid.decode()])
        logger.info("Stopped all server processes")
    except subprocess.CalledProcessError:
        logger.info(f"No processes found using port {PORT}")


class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        logger.info(f"Request: {request.method} {request.url}")
        logger.info(f"From: {request.client.host}")
        logger.info(f"Headers: {request.headers}")
        body = await request.body()
        logger.info(f"Body: {body.decode()}")
        return await call_next(request)


async def configure_local_webhooks() -> None:
    ngrok_connection = ngrok.connect(addr=f"{LOCAL_URL}:{PORT}", proto="http")
    logger.info(f"Ngrok public URL: {ngrok_connection.public_url}")

    webhook = f"{ngrok_connection.public_url}/message"
    _telegram = Telegram.from_config(config.MESSAGING_CONFIG.TELEGRAM)
    _bird = BirdSMSProvider.from_config(config.MESSAGING_CONFIG.BIRD)

    if bird_dev_channel_id := os.getenv("BIRD_DEV_CHANNEL_ID"):
        _bird.set_channel_id(bird_dev_channel_id)

    await asyncio.gather(
        _telegram.register_webhook(webhook),
        _bird.register_webhook(event="sms.inbound", webhook_url=webhook),
    )

    logger.info("Ngrok and webhooks successfully set up!")


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    ngrok.kill()
    redis_manager.close()


app = FastAPI(lifespan=lifespan)
app.add_middleware(LoggingMiddleware)
app.include_router(message_router)
app.include_router(signup_router)
app.include_router(cron_router)

"""
Gunicorn is used in local to test concurrency manager (since multiple workers)
To view ports run: ps aux | grep gunicorn
To kill gunicorn run: pkill -f gunicorn

Celery
View celery tasks via Flower: celery -A zootopia.server.celery.celery flower

celery -A zootopia.server.celery.celery worker --loglevel=info -n worker1@%h

TODO: add celery run command to prod
"""
if __name__ == "__main__":
    use_gunicorn = False

    asyncio.run(configure_local_webhooks())

    stop_existing_servers()

    # Start Celery server
    celery_command = [
        "celery",
        "-A",
        "zootopia.server.celery.celery",
        "worker",
        "--loglevel=info",
        "-n",
        "worker1@%h",
    ]
    subprocess.Popen(celery_command)

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
            f"{LOCAL_URL}:{PORT}",
        ]
        subprocess.Popen(gunicorn_command)
    else:
        # Start Uvicorn server
        import uvicorn

        uvicorn.run("main:app", host=LOCAL_URL, port=PORT, reload=True)
