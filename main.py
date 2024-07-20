"""Starts FastAPI server to receive messages"""
import asyncio
import os
from contextlib import asynccontextmanager
from pyngrok import ngrok
import uvicorn
from typing import Optional

from fastapi import FastAPI
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from config.config import config
from zootopia.platform.telegram.telegram import Telegram
from zootopia.platform.sms.bird import BirdSMSProvider
from zootopia.core.routers.message import router as message_router
from zootopia.core.logger import logger


class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        print(f"Request: {request.method} {request.url}")
        print(f"From: {request.client.host}")
        print(f"Headers: {request.headers}")
        body = await request.body()
        print(f"Body: {body.decode()}")
        response = await call_next(request)
        return response

async def configure_webhooks():
    ngrok_connection = ngrok.connect(addr="127.0.0.1:8000", proto="http")
    print(f"Ngrok public URL: {ngrok_connection.public_url}")

    _telegram = Telegram.from_config(config.MESSAGING_CONFIG.TELEGRAM)
    _bird = BirdSMSProvider.from_config(config.MESSAGING_CONFIG.BIRD)
    webhook = f"{ngrok_connection.public_url}/message"
    await asyncio.gather(
        _telegram.register_webhook(webhook), 
        _bird.register_webhook(event="sms.inbound", webhook_url=webhook),
    )

    print("\033[92m\033[1mNgrok and webhooks successfully set up!\033[0m")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting application.")
    yield 

    # Shutdown
    logger.info("Closing application.")
    ngrok.kill()

# Loading FastAPI app
app = FastAPI(lifespan=lifespan)
app.add_middleware(LoggingMiddleware)
app.include_router(message_router)

if __name__ == "__main__":
    asyncio.run(configure_webhooks())
    uvicorn.run("run:app", host="127.0.0.1", port=8000, reload=True)
  