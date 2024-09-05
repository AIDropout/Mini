from celery import Celery

app = Celery("mini")

app.config_from_object("mini.server.celery.celeryconfig")

app.autodiscover_tasks(
    [
        "mini.controller.task.task_processor",
        "mini.server.celery.cron.proactive_messages",
    ]
)
