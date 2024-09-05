import argparse
import asyncio
import subprocess
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pyngrok import ngrok

from config.config import config
from mini.api import router as api_router
from mini.core.logger import logger
from mini.server.redis import RedisManager
from mini.utils.utils import configure_local_webhooks, stop_existing_processes

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
                "mini.server.celery.celery",
                "worker",
                "-n",
                "worker1@%h",
                "--loglevel=ERROR",
                "--beat",
            ],
        )

        # Start Celery beat
        if config.ENABLE_CELERY_BEAT:
            celery_beat_process = subprocess.Popen(
                [
                    "celery",
                    "-A",
                    "mini.server.celery.celery",
                    "beat",
                    "--loglevel=INFO",
                ],
            )

    yield
    if celery_worker_process:
        celery_worker_process.terminate()
    if celery_beat_process:
        celery_beat_process.terminate()
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
- View celery tasks via Flower: celery -A mini.server.celery.celery flower

- To manually start Celery, open a new terminal: celery -A mini.server.celery.celery worker -n worker1@%h

"""

if __name__ == "__main__":
    """This main function is ONLY called when developing and running python main.py. 
    (Prod has a separate run command on Render)"""

    LOCAL_URL = "127.0.0.1"
    PORT = 8000
    USE_GUNICORN = False

    # Set up a local server with a public url via ngrok
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
