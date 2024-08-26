import asyncio
import subprocess
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from pyngrok import ngrok
from zootopia.api import router as api_router
from zootopia.core.logger import logger
from zootopia.manager.messaging import TelegramManager, BirdManager
from zootopia.server.redis import RedisManager
from config.config import config
from fastapi.middleware.cors import CORSMiddleware


LOCAL_URL = "127.0.0.1"
PORT = 8000
USE_GUNICORN = False


def stop_existing_processes():
    """Stops all local server processes for main.py"""

    try:
        pids = subprocess.check_output(["lsof", "-t", f"-i:{PORT}"]).split()
        for pid in pids:
            logger.info(f"Killing process {pid.decode()} using port {PORT}")
            subprocess.run(["kill", "-9", pid.decode()])
        logger.info("Stopped all server processes")
    except subprocess.CalledProcessError:
        logger.info(f"No processes found using port {PORT}")


async def configure_local_webhooks() -> None:
    """Sets up an Ngrok public URL, and directs received Bird/Telegram messages to the URL"""

    ngrok_connection = ngrok.connect(addr=f"{LOCAL_URL}:{PORT}", proto="http")
    logger.info(f"Ngrok public URL: {ngrok_connection.public_url}")

    webhook = f"{ngrok_connection.public_url}/rooms/respond"
    _telegram = TelegramManager()
    _bird = BirdManager()

    _bird.set_sender(config.BIRD_DEV_CHANNEL_ID)

    await asyncio.gather(
        _telegram.register_webhook(webhook),
        _bird.register_webhook(event="sms.inbound", webhook_url=webhook),
    )

    logger.info("Ngrok and webhooks successfully set up!")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Life cycle of FastAPI server"""
    celery_worker_process = None
    # Before Start
    redis_manager = RedisManager()
    redis_manager.initialize()
    if config.ENVIRONMENT == "local":
        # Start Celery worker
        celery_worker_process = subprocess.Popen(
            [
                "celery",
                "-A",
                "zootopia.server.celery.celery",
                "worker",
                "-n",
                "worker1@%h",
                "--loglevel=ERROR",
            ],
        )

    yield
    # After end
    celery_worker_process.terminate()
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

    # logger.info(f"Response status: {response.status_code}")
    return response


"""
How everything is setup:

In production (Render.com), the start command is starting the celery servers and gunicorn workers

In local, we can either use uvicorn or gunicorn (gunicorn to simulate prod environment) by setting USE_GUNICORN: bool

To start local, run python main.py

Helpful commands:
- To view gunicorn ports run: ps aux | grep gunicorn
- To kill gunicorn run: pkill -f gunicorn
Flower (Flower hosts a localhost dashboard to view status of Celery tasks):
- export PYTHONPATH=$PYTHONPATH:/Users/chris/Desktop/Untitled
- View celery tasks via Flower: celery -A zootopia.server.celery.celery flower

- To manually start Celery, open a new terminal: celery -A zootopia.server.celery.celery worker -n worker1@%h

"""
if __name__ == "__main__":
    """This main function is ONLY called when developing and running python main.py. 
    
    (Prod has a separate run command on Render)"""

    # Set up a local server with a public url via ngrok
    asyncio.run(configure_local_webhooks())

    # Stops all existing servers
    stop_existing_processes()

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
