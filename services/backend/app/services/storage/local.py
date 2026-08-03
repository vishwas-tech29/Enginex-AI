import shutil
from pathlib import Path
from typing import BinaryIO

from app.services.storage.base import DownloadTarget, FileStorage


class LocalFileStorage(FileStorage):
    """Disk-backed storage for local development.

    Mirrors the S3 key layout (`projects/<id>/<file_id>/v<n>/<name>`) under a
    root directory so swapping in `S3Storage` later requires no key changes.
    """

    def __init__(self, root: str):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def _path_for(self, key: str) -> Path:
        path = (self.root / key).resolve()
        if self.root.resolve() not in path.parents and path != self.root.resolve():
            raise ValueError("Invalid storage key")
        return path

    def save(self, key: str, fileobj: BinaryIO) -> int:
        path = self._path_for(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        fileobj.seek(0)
        with open(path, "wb") as out:
            shutil.copyfileobj(fileobj, out)
        return path.stat().st_size

    def delete(self, key: str) -> None:
        path = self._path_for(key)
        path.unlink(missing_ok=True)

    def get_download_target(self, key: str, expires_in: int = 3600) -> DownloadTarget:
        path = self._path_for(key)
        return DownloadTarget(kind="path", value=str(path))
