"""Starts FastAPI server to receive messages"""
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

from zootopia.server.background import BackgroundRunner


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
    
    if bird_dev_channel_id := os.getenv('BIRD_DEV_CHANNEL_ID'):
        _bird.set_channel_id(bird_dev_channel_id)
    
    await asyncio.gather(
        _telegram.register_webhook(webhook),
        _bird.register_webhook(event="sms.inbound", webhook_url=webhook),
    )

    logger.info("Ngrok and webhooks successfully set up!")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Runs continously as long as the server is up
    runner = BackgroundRunner(config)
    background_task = asyncio.create_task(runner.run())
    yield
    # Cleanup
    ngrok.kill()
    background_task.cancel()
    try:
        await background_task
    except asyncio.CancelledError:
        pass

app = FastAPI(lifespan=lifespan)
app.add_middleware(LoggingMiddleware)
app.include_router(message_router)
app.include_router(signup_router)
app.include_router(cron_router)

""" Run python main.py

Gunicorn is used in local to test concurrency manager (since multiple workers)

To kill gunicorn run: pkill -f gunicorn

To view ports run: ps aux | grep gunicorn
"""
if __name__ == "__main__":
    use_gunicorn = True
    asyncio.run(configure_local_webhooks())

    if use_gunicorn:
        gunicorn_command = [
            "gunicorn",
            "-w", "4",
            "-k", "uvicorn.workers.UvicornWorker",
            "main:app",
            "--bind", "127.0.0.1:8000",
        ]
        try:
            logger.info("Starting Gunicorn server...")
            subprocess.run(gunicorn_command, check=True)
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to start Gunicorn. Error: {e}")
        except FileNotFoundError:
            logger.error("Gunicorn command not found. Make sure it's installed and in your PATH.")
    else:
        uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)


