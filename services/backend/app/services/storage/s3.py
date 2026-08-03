from typing import BinaryIO

import boto3

from app.services.storage.base import DownloadTarget, FileStorage


class S3Storage(FileStorage):
    """S3 (or S3-compatible, e.g. MinIO) backed storage."""

    def __init__(self, bucket: str, endpoint_url: str, access_key: str, secret_key: str, region: str):
        self.bucket = bucket
        self.client = boto3.client(
            "s3",
            endpoint_url=endpoint_url,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name=region,
        )

    def save(self, key: str, fileobj: BinaryIO) -> int:
        fileobj.seek(0, 2)
        size = fileobj.tell()
        fileobj.seek(0)
        self.client.upload_fileobj(fileobj, self.bucket, key)
        return size

    def delete(self, key: str) -> None:
        self.client.delete_object(Bucket=self.bucket, Key=key)

    def get_download_target(self, key: str, expires_in: int = 3600) -> DownloadTarget:
        url = self.client.generate_presigned_url(
            "get_object",
            Params={"Bucket": self.bucket, "Key": key},
            ExpiresIn=expires_in,
        )
        return DownloadTarget(kind="url", value=url)
