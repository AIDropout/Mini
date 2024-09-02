from .s3 import S3FileStore

singleton = S3FileStore()

def get_file_store() -> S3FileStore:
    return singleton