from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import BinaryIO, Literal


@dataclass
class DownloadTarget:
    """Where a client should fetch an object from.

    `path` — a local filesystem path the route should stream via FileResponse.
    `url` — a (possibly presigned) URL the route should redirect to.
    """

    kind: Literal["path", "url"]
    value: str


class FileStorage(ABC):
    @abstractmethod
    def save(self, key: str, fileobj: BinaryIO) -> int:
        """Persist `fileobj` under `key`. Returns size in bytes."""

    @abstractmethod
    def delete(self, key: str) -> None:
        """Remove the object at `key`, if it exists."""

    @abstractmethod
    def get_download_target(self, key: str, expires_in: int = 3600) -> DownloadTarget:
        """Return where a client should fetch `key` from."""
