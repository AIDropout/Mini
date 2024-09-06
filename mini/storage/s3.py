import io
from datetime import timedelta

from minio import Minio

from config.config import config

from .files import FileStore

AWS_S3_ENDPOINT = "s3.amazonaws.com"


class S3FileStore(FileStore):
    def __init__(self, endpoint: str = AWS_S3_ENDPOINT) -> None:
        access_key = config.AWS_S3_CONFIG.access_key
        secret_key = config.AWS_S3_CONFIG.secret_access_key
        self.bucket = config.AWS_S3_CONFIG.bucket
        self.client = Minio(endpoint, access_key, secret_key)

    def write(self, path: str, contents: bytes, content_type: str) -> None:
        length = len(contents)
        self.client.put_object(
            self.bucket, path, io.BytesIO(contents), length, content_type=content_type
        )

    def read(self, path: str) -> bytes:
        return self.client.get_object(self.bucket, path).data

    def list(self, path: str) -> list[str]:
        return [obj.object_name for obj in self.client.list_objects(self.bucket, path)]

    def delete(self, path: str) -> None:
        self.client.remove_object(self.bucket, path)

    def generate_presigned_url(
        self, path: str, content_type: str, expiration: int = 3600
    ) -> str:
        """
        Generate a pre-signed URL for an S3 object.
        :param path: The S3 object key (file path in the bucket).
        :param expiration: Time in seconds for the pre-signed URL to remain valid.
        :return: The pre-signed URL as a string.
        """
        return self.client.presigned_get_object(
            self.bucket,
            path,
            expires=timedelta(seconds=expiration),
            response_headers={"response-content-type": content_type},
        )
