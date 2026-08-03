import { useEffect, useMemo, useRef, useState } from 'react';
import * as Y from 'yjs';

import { storage } from '@/services/storage';
import { bytesToHex, hexToBytes } from '@/modules/editor/utils/hex';
import { PresenceEntry } from '@/modules/editor/types';

const REMOTE_ORIGIN = 'remote';

/**
 * Connects a Yjs document to the backend's per-file collaboration room
 * (see services/backend/app/websockets/manager.py). The wire protocol is a
 * custom JSON envelope, not the npm `y-websocket` binary protocol — but the
 * `update` payloads ARE genuine Yjs updates, so concurrent edits merge via
 * real CRDT semantics.
 */
export function useYjsEditor(fileId: string | undefined) {
  const ydoc = useMemo(() => new Y.Doc(), []);
  const [presence, setPresence] = useState<PresenceEntry[]>([]);
  const [isSynced, setIsSynced] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    if (!fileId) return;

    const token = storage.getAccessToken();
    const wsBase = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000';
    const ws = new WebSocket(`${wsBase}/ws/files/${fileId}?token=${token ?? ''}`);
    wsRef.current = ws;
    setIsSynced(false);

    ws.onmessage = (event) => {
      const message = JSON.parse(event.data as string);

      if (message.type === 'init') {
        Y.applyUpdate(ydoc, hexToBytes(message.state), REMOTE_ORIGIN);
        setPresence(message.presence);
        setIsSynced(true);
      } else if (message.type === 'update') {
        Y.applyUpdate(ydoc, hexToBytes(message.update), REMOTE_ORIGIN);
      } else if (message.type === 'presence') {
        setPresence(message.presence);
      }
    };

    const handleLocalUpdate = (update: Uint8Array, origin: unknown) => {
      if (origin === REMOTE_ORIGIN) return; // don't echo back updates we just applied
      if (ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ type: 'update', update: bytesToHex(update) }));
      }
    };
    ydoc.on('update', handleLocalUpdate);

    return () => {
      ydoc.off('update', handleLocalUpdate);
      ws.close();
      wsRef.current = null;
    };
  }, [fileId, ydoc]);

  function sendCursor(position: { x: number; y: number }) {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: 'cursor', position }));
    }
  }

  function sendSelection(selection: unknown) {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: 'selection', selection }));
    }
  }

  return { ydoc, presence, isSynced, sendCursor, sendSelection };
}
