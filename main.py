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

from zootopia.server.background import process_scheduled_responses

class ServerManager:
    @classmethod
    def run_redis(cls) -> None:
        try:
            subprocess.run(["redis-server", "--daemonize", "yes"], check=True, capture_output=True, text=True)
            logger.info("Redis started successfully.")
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to start Redis. Error: {e.stderr}")
        except FileNotFoundError:
            logger.error("Redis-server command not found. Make sure it's installed and in your PATH.")
    
    @classmethod
    def close_redis(cls) -> None:
        try:
            subprocess.run(["redis-cli", "shutdown"], check=True, capture_output=True, text=True)
            logger.info("Redis stopped successfully.")
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to stop Redis. Error: {e.stderr}")
        except FileNotFoundError:
            logger.error("Redis-cli command not found. Make sure it's installed and in your PATH.")
        logger.info("Cleanup completed.")
    
    @classmethod
    def run_gunicorn(cls, app: str, workers: int = 4, port: int = 8000) -> None:
        command = [
            "gunicorn",
            "-w", str(workers),
            "-k", "uvicorn.workers.UvicornWorker",
            f"{app}:app",
            "--bind", f"127.0.0.1:{port}",
        ]
        try:
            subprocess.run(command)
            logger.info("Gunicorn started successfully.")
        except FileNotFoundError:
            logger.error("Gunicorn command not found. Make sure it's installed and in your PATH.")

    @classmethod
    def close_gunicorn(cls) -> None:
        try:
            subprocess.run(["pkill", "-f", "gunicorn"], check=True, capture_output=True, text=True)
            logger.info("Gunicorn stopped successfully.")
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to stop Gunicorn. Error: {e.stderr}")

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
    background_task = asyncio.create_task(process_scheduled_responses())

    yield
    # After
    ngrok.kill()
    # Cleanup: Cancel the background task when the app is shutting down
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

if __name__ == "__main__":
    use_gunicorn = False

    if os.getenv('ENVIRONMENT', '').lower() == 'local':
        asyncio.run(configure_local_webhooks())

    ServerManager.close_redis()
    ServerManager.run_redis()
    
    if use_gunicorn:
        ServerManager.close_gunicorn()
        ServerManager.run_gunicorn(app="main")
    else:
        uvicorn.run(f"main:app", host="127.0.0.1", port=8000, reload=True)

    # gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app
    # ps aux | grep gunicorn
    # pkill -f gunicorn



