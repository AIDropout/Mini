import asyncio
import os
import subprocess
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
import uvicorn
from pyngrok import ngrok
from starlette.middleware.base import BaseHTTPMiddleware
from config.config import config
from zootopia.platform.telegram.telegram import Telegram
from zootopia.platform.sms.bird import BirdSMSProvider
from zootopia.core.logger import logger
from zootopia.core.routers import signup_router, message_router, cron_router

class ServerManager:
    def __init__(self):
        self.processes = []

    def start_gunicorn(self):
        gunicorn_command = [
            "gunicorn",
            "-w",
            "4",
            "-k",
            "uvicorn.workers.UvicornWorker",
            "main:app",
            "--bind",
            "127.0.0.1:8000",
        ]
        gunicorn_process = subprocess.Popen(gunicorn_command)
        self.processes.append(gunicorn_process)
        logger.info("Started Gunicorn server")

    def start_celery(self):
        celery_command = [
            "celery",
            "-A",
            "zootopia.server.celery.celery_app",
            "worker",
            "--loglevel=info",
        ]
        celery_process = subprocess.Popen(celery_command)
        self.processes.append(celery_process)
        logger.info("Started Celery worker")

    def stop_servers(self):
        for process in self.processes:
            process.terminate()

        for process in self.processes:
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()

        logger.info("Stopped all server processes")


class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        logger.info(f"Request: {request.method} {request.url}")
        logger.info(f"From: {request.client.host}")
        logger.info(f"Headers: {request.headers}")
        body = await request.body()
        logger.info(f"Body: {body.decode()}")
        return await call_next(request)


async def configure_local_webhooks() -> None:
    ngrok_connection = ngrok.connect(addr="127.0.0.1:8000", proto="http")
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


app = FastAPI(lifespan=lifespan)
app.add_middleware(LoggingMiddleware)
app.include_router(message_router)
app.include_router(signup_router)
app.include_router(cron_router)

""" Run python main.py

Gunicorn is used in local to test concurrency manager (since multiple workers)

To kill gunicorn run: pkill -f gunicorn

To view ports run: ps aux | grep gunicorn

To run celery: celery -A tasks worker --loglevel=info

TODO: add celery run command to prod
"""
if __name__ == "__main__":    
    use_gunicorn = False

    asyncio.run(configure_local_webhooks())

    server_manager = ServerManager()
    server_manager.start_celery() 

    if use_gunicorn:
        server_manager.start_gunicorn()
    else:
        uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)