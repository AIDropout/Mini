from celery import Celery

app = Celery("mini")

app.config_from_object("mini.server.celery.celeryconfig")

app.autodiscover_tasks(
    [
        "mini.server.celery.tasks.send_message.send_message",
        "mini.server.celery.tasks.run_cron.run_cron",
        "mini.server.celery.tasks.process_session.process_session",
    ]
)
