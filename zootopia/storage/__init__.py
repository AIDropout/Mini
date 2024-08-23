from config.config import config

from .files import FileStore
from .local import LocalFileStore
from .memory import InMemoryFileStore
from .s3 import S3FileStore


def _get_file_store() -> FileStore:
    if config.FILE_STORE == "local":
        return LocalFileStore(config.FILE_STORE_PATH)
    elif config.FILE_STORE == "s3":
        return S3FileStore()
    return InMemoryFileStore()


singleton = _get_file_store()


def get_file_store() -> FileStore:
    return singleton
