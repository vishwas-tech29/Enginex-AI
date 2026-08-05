import { useRouter } from 'next/router';
import { ChangeEvent, useEffect, useState } from 'react';

import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { Card } from '@/components/common/Card';
import { DashboardLayout } from '@/components/layout/DashboardLayout';
import { PCBEditor } from '@/modules/pcb-editor';
import { useFileUpload } from '@/modules/projects/hooks/useFileUpload';
import { PCBBoard, pcbApi } from '@/services/api/pcb';
import { filesApi, ProjectFile } from '@/services/api/files';

function PCBEditorPageContent() {
  const router = useRouter();
  const { id } = router.query;
  const projectId = typeof id === 'string' ? id : undefined;

  const [files, setFiles] = useState<ProjectFile[] | null>(null);
  const [activeFileId, setActiveFileId] = useState<string | null>(null);
  const { upload, isUploading, progress } = useFileUpload();

  const [boards, setBoards] = useState<PCBBoard[]>([]);
  const [activeBoardId, setActiveBoardId] = useState<string | null>(null);
  const [isCreatingBoard, setIsCreatingBoard] = useState(false);
  const [boardWidth, setBoardWidth] = useState(80);
  const [boardHeight, setBoardHeight] = useState(60);

  useEffect(() => {
    if (!projectId) return;
    void filesApi.listForProject(projectId).then((data) => {
      setFiles(data);
      if (data.length > 0) setActiveFileId((current) => current ?? data[0]?.id ?? null);
    });
  }, [projectId]);

  useEffect(() => {
    if (!activeFileId) {
      setBoards([]);
      setActiveBoardId(null);
      return;
    }
    void pcbApi.listBoards(activeFileId).then((data) => {
      setBoards(data);
      setActiveBoardId((current) => current ?? data[0]?.id ?? null);
    });
  }, [activeFileId]);

  async function handleUpload(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    if (!file || !projectId) return;
    const created = await upload(file, projectId);
    // The initial listForProject() fetch and this optimistic update can
    // resolve in either order (both are in-flight after upload), so dedupe
    // by id instead of assuming `current` never already has this file —
    // otherwise a same-id entry can render twice with a duplicate React key.
    setFiles((current) => [created, ...(current ?? []).filter((f) => f.id !== created.id)]);
    setActiveFileId(created.id);
    event.target.value = '';
  }

  async function handleCreateBoard() {
    if (!activeFileId) return;
    setIsCreatingBoard(true);
    try {
      const board = await pcbApi.createBoard(activeFileId, `Board ${boards.length + 1}`, boardWidth, boardHeight);
      setBoards((current) => [...current, board]);
      setActiveBoardId(board.id);
    } finally {
      setIsCreatingBoard(false);
    }
  }

  function handleBoardChange(updated: PCBBoard) {
    setBoards((current) => current.map((b) => (b.id === updated.id ? updated : b)));
  }

  const activeBoard = boards.find((b) => b.id === activeBoardId) ?? null;

  return (
    <DashboardLayout>
      <div className="space-y-4">
        <div>
          <h1 className="text-2xl font-semibold text-slate-900">PCB editor</h1>
          <p className="text-sm text-slate-600">
            {activeFileId ? 'Place components, route copper, and check the design.' : 'Upload a design file to start editing.'}
          </p>
        </div>

        {!activeFileId ? (
          <Card>
            <div className="flex flex-col items-center gap-3 py-10 text-center">
              <p className="text-sm text-slate-600">
                This project doesn&apos;t have any files yet — upload one to start a PCB layout.
              </p>
              <label>
                <input type="file" className="hidden" onChange={handleUpload} disabled={isUploading} />
                <span className="inline-flex cursor-pointer items-center rounded-md bg-brand-600 px-4 py-2 text-sm font-medium text-white">
                  {isUploading ? `Uploading… ${progress}%` : 'Upload a file'}
                </span>
              </label>
            </div>
          </Card>
        ) : !activeBoard ? (
          <Card>
            <div className="flex flex-wrap items-end gap-3 py-6">
              <div>
                <h2 className="text-sm font-semibold text-slate-900">No boards yet</h2>
                <p className="text-xs text-slate-500">Create a board to start placing components.</p>
              </div>
              <label className="text-xs text-slate-600">
                Width (mm)
                <input
                  type="number" min={1} value={boardWidth}
                  onChange={(event) => setBoardWidth(Number(event.target.value) || 1)}
                  className="mt-1 block w-24 rounded-md border border-slate-300 px-2 py-1 text-sm"
                />
              </label>
              <label className="text-xs text-slate-600">
                Height (mm)
                <input
                  type="number" min={1} value={boardHeight}
                  onChange={(event) => setBoardHeight(Number(event.target.value) || 1)}
                  className="mt-1 block w-24 rounded-md border border-slate-300 px-2 py-1 text-sm"
                />
              </label>
              <button
                type="button"
                onClick={handleCreateBoard}
                disabled={isCreatingBoard}
                className="rounded-md bg-brand-600 px-3 py-2 text-sm font-medium text-white disabled:opacity-60"
              >
                {isCreatingBoard ? 'Creating…' : '+ New board'}
              </button>
            </div>
          </Card>
        ) : (
          <Card>
            <PCBEditor board={activeBoard} onBoardChange={handleBoardChange} />
          </Card>
        )}

        {boards.length > 1 && (
          <div className="flex flex-wrap gap-2">
            {boards.map((board) => (
              <button
                key={board.id}
                type="button"
                onClick={() => setActiveBoardId(board.id)}
                className={`rounded-md border px-3 py-1.5 text-sm ${
                  board.id === activeBoardId
                    ? 'border-brand-600 bg-brand-50 text-brand-700'
                    : 'border-slate-200 bg-white text-slate-600'
                }`}
              >
                {board.name}
              </button>
            ))}
          </div>
        )}

        {files && files.length > 0 && (
          <div className="flex flex-wrap gap-2">
            {files.map((file) => (
              <button
                key={file.id}
                type="button"
                onClick={() => setActiveFileId(file.id)}
                className={`rounded-md border px-3 py-1.5 text-sm ${
                  file.id === activeFileId
                    ? 'border-brand-600 bg-brand-50 text-brand-700'
                    : 'border-slate-200 bg-white text-slate-600'
                }`}
              >
                {file.name}
              </button>
            ))}
            <label>
              <input type="file" className="hidden" onChange={handleUpload} disabled={isUploading} />
              <span className="inline-flex cursor-pointer items-center rounded-md border border-slate-300 bg-white px-3 py-1.5 text-sm text-slate-700">
                {isUploading ? `Uploading… ${progress}%` : '+ Add file'}
              </span>
            </label>
          </div>
        )}
      </div>
    </DashboardLayout>
  );
}

export default function PCBEditorPage() {
  return (
    <ProtectedRoute>
      <PCBEditorPageContent />
    </ProtectedRoute>
  );
}
