from celery import Celery
from config.config import config
from celery import shared_task
from zootopia.context import MessageContextManager, CronContextManager
from zootopia.core.schema import RespondTask, RemindTask, ReviveTask, TaskType
from zootopia.agent.agent import Agent
from config.config import config
from zootopia.core.logger import logger
import json
import asyncio


celery_app = Celery("zootopia")

celery_app.config_from_object("zootopia.server.celery.celeryconfig")

celery_app.autodiscover_tasks(['zootopia.server.celery'])

