from zootopia.core.config import config

broker_url = config.REDIS_URL
result_backend = config.REDIS_URL

task_serializer = "json"
result_serializer = "json"
accept_content = ["json"]
timezone = "UTC"
enable_utc = True
worker_hijack_root_logger = False
