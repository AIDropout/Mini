from celery import Celery

app = Celery("mini")

app.config_from_object("mini.server.celery.celeryconfig")

app.autodiscover_tasks(
    ["mini.messaging.send_message.send_message", "mini.server.celery.cron.run_jobs"]
)
