"""Real-time collaboration over WebSockets, synced with a Yjs CRDT per file.

Wire protocol is a custom JSON envelope (not the npm `y-websocket` binary
sync/awareness protocol) — see docs/architecture/complete-architecture.md for
the rationale. The payloads inside `update` messages ARE genuine Yjs update
bytes (produced/consumed by `y-py`, the same CRDT engine behind the `yjs` JS
library), so conflict resolution is real CRDT merging, not last-write-wins.

Message shapes:
  Client -> Server:
    {"type": "update", "update": "<hex-encoded Yjs update>"}
    {"type": "cursor", "position": {...}}
    {"type": "selection", "selection": {...}}
  Server -> Client:
    {"type": "init", "state": "<hex>", "presence": [...]}
    {"type": "update", "update": "<hex>"}          # relayed from a peer
    {"type": "presence", "presence": [...]}
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

import y_py as Y
from fastapi import WebSocket
from sqlalchemy.orm import Session

from app.models.collab import YDocSnapshot


@dataclass
class ConnectionState:
    user_id: str
    name: str
    cursor: dict | None = None
    selection: dict | None = None


@dataclass
class _Room:
    ydoc: Y.YDoc
    connections: dict[WebSocket, ConnectionState] = field(default_factory=dict)


class ConnectionManager:
    def __init__(self) -> None:
        self.rooms: dict[str, _Room] = {}

    def _room_key(self, file_id: uuid.UUID) -> str:
        return str(file_id)

    async def connect(
        self, file_id: uuid.UUID, websocket: WebSocket, user, db: Session
    ) -> None:
        await websocket.accept()
        key = self._room_key(file_id)

        if key not in self.rooms:
            ydoc = Y.YDoc()
            snapshot = db.get(YDocSnapshot, file_id)
            if snapshot is not None:
                Y.apply_update(ydoc, snapshot.state)
            self.rooms[key] = _Room(ydoc=ydoc)

        room = self.rooms[key]
        room.connections[websocket] = ConnectionState(user_id=str(user.id), name=user.name)

        await websocket.send_json(
            {
                "type": "init",
                "state": Y.encode_state_as_update(room.ydoc).hex(),
                "presence": self._presence_list(room),
            }
        )
        await self.broadcast_presence(file_id)

    async def disconnect(self, file_id: uuid.UUID, websocket: WebSocket, db: Session) -> None:
        key = self._room_key(file_id)
        room = self.rooms.get(key)
        if room is None:
            return

        room.connections.pop(websocket, None)

        if not room.connections:
            self._persist(file_id, room, db)
            del self.rooms[key]
        else:
            await self.broadcast_presence(file_id)

    def _persist(self, file_id: uuid.UUID, room: _Room, db: Session) -> None:
        state = Y.encode_state_as_update(room.ydoc)
        now = datetime.now(timezone.utc)
        snapshot = db.get(YDocSnapshot, file_id)
        if snapshot is None:
            db.add(YDocSnapshot(file_id=file_id, state=state, updated_at=now))
        else:
            snapshot.state = state
            snapshot.updated_at = now
        db.commit()

    async def handle_message(
        self, file_id: uuid.UUID, websocket: WebSocket, message: dict[str, Any]
    ) -> None:
        key = self._room_key(file_id)
        room = self.rooms.get(key)
        if room is None:
            return

        msg_type = message.get("type")

        if msg_type == "update":
            update = bytes.fromhex(message["update"])
            Y.apply_update(room.ydoc, update)
            await self._broadcast(room, {"type": "update", "update": update.hex()}, exclude=websocket)

        elif msg_type == "cursor":
            state = room.connections.get(websocket)
            if state:
                state.cursor = message.get("position")
            await self.broadcast_presence(file_id)

        elif msg_type == "selection":
            state = room.connections.get(websocket)
            if state:
                state.selection = message.get("selection")
            await self.broadcast_presence(file_id)

    async def broadcast_presence(self, file_id: uuid.UUID) -> None:
        key = self._room_key(file_id)
        room = self.rooms.get(key)
        if room is None:
            return
        await self._broadcast(room, {"type": "presence", "presence": self._presence_list(room)})

    def _presence_list(self, room: _Room) -> list[dict]:
        return [
            {
                "user_id": state.user_id,
                "name": state.name,
                "cursor": state.cursor,
                "selection": state.selection,
            }
            for state in room.connections.values()
        ]

    async def _broadcast(
        self, room: _Room, message: dict[str, Any], exclude: WebSocket | None = None
    ) -> None:
        for connection in list(room.connections):
            if connection is exclude:
                continue
            await connection.send_json(message)


manager = ConnectionManager()
