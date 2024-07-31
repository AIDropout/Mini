from celery import Celery
# from zootopia.controller.tasks.tasks import *

app = Celery("zootopia")

app.config_from_object("zootopia.server.celery.celeryconfig")

# app.autodiscover_tasks(["zootopia.controller.tasks.tasks"])
