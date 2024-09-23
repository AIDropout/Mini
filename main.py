"""
Main entry point for the fastapi application.
Sets up the application with its routes, middleware, and event handlers.
"""

import asyncio
import subprocess
from contextlib import asynccontextmanager

import uvicorn
from fastapi import APIRouter, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pyngrok import ngrok

from config.config import config
from mini.core.logger import get_logger
from mini.dashboard import endpoint as dashboard_endpoint
from mini.database.agents import endpoint as agents_endpoint
from mini.database.rooms import endpoint as rooms_endpoint
from mini.database.users import endpoint as users_endpoint
from mini.messaging.bird import endpoint as bird_endpoint
from mini.messaging.bird.verification import endpoint as smsotp_endpoint
from mini.messaging.instagram import endpoint as instagram_endpoint
from mini.payment import endpoint as payment_endpoint
from mini.server.redis import RedisManager
from mini.server.schedule import endpoint as proactive_endpoint
from mini.server.schedule.scheduler import TaskScheduler
from mini.utils.utils import configure_local_webhooks, stop_existing_processes

logger = get_logger(__name__)

task_scheduler = TaskScheduler(db_url=config.SCHEDULER_DB_URL)
task_scheduler.initialize()


@asynccontextmanager
async def lifespan(_: FastAPI):
    """Life cycle of FastAPI server."""
    redis_manager = RedisManager()
    redis_manager.initialize()

    if config.ENVIRONMENT == "local":
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

    task_scheduler.scheduler.shutdown(wait=False)
    subprocess.run(["pkill", "-f", "celery"], check=False)
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

router = APIRouter()
router.include_router(bird_endpoint.router)
router.include_router(payment_endpoint.router)
router.include_router(smsotp_endpoint.router)
router.include_router(dashboard_endpoint.router)
router.include_router(rooms_endpoint.router)
router.include_router(agents_endpoint.router)
router.include_router(users_endpoint.router)
router.include_router(instagram_endpoint.router)
router.include_router(proactive_endpoint.router)

app.include_router(router)


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
