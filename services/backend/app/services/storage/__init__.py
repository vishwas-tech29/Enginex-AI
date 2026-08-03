from functools import lru_cache

from app.config import settings
from app.services.storage.base import DownloadTarget, FileStorage
from app.services.storage.local import LocalFileStorage

__all__ = ["FileStorage", "DownloadTarget", "get_storage"]


@lru_cache
def get_storage() -> FileStorage:
    if settings.storage_backend == "s3":
        from app.services.storage.s3 import S3Storage

        return S3Storage(
            bucket=settings.s3_bucket,
            endpoint_url=settings.s3_endpoint,
            access_key=settings.s3_access_key,
            secret_key=settings.s3_secret_key,
            region=settings.s3_region,
        )
    return LocalFileStorage(settings.storage_root)
