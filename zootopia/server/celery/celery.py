from celery import Celery

app = Celery("zootopia")

app.config_from_object("zootopia.server.celery.celeryconfig")

app.autodiscover_tasks(["zootopia.controller.tasks.task_processor"])

