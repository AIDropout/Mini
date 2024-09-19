from celery import Celery

app = Celery("mini")

app.config_from_object("mini.server.celery.celeryconfig")

app.autodiscover_tasks(
    [
        "mini.controller.run_agent",
        "mini.server.celery.cron.proactive_messages",
    ]
)
