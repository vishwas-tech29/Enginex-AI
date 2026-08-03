import dynamic from 'next/dynamic';
import { useRouter } from 'next/router';
import { ChangeEvent, useEffect, useState } from 'react';

import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { Card } from '@/components/common/Card';
import { DashboardLayout } from '@/components/layout/DashboardLayout';
import { useFileUpload } from '@/modules/projects/hooks/useFileUpload';
import { Viewport3D } from '@/modules/cad-editor/components/Viewport3D';
import { filesApi, ProjectFile } from '@/services/api/files';

const Canvas2D = dynamic(
  () => import('@/modules/editor/components/Canvas2D').then((mod) => mod.Canvas2D),
  {
    ssr: false,
    loading: () => (
      <div className="flex h-48 items-center justify-center rounded-md border border-slate-200 bg-slate-50 text-sm text-slate-500">
        Loading editor…
      </div>
    ),
  },
);

function CADEditorPageContent() {
  const router = useRouter();
  const { id } = router.query;
  const projectId = typeof id === 'string' ? id : undefined;

  const [files, setFiles] = useState<ProjectFile[] | null>(null);
  const [activeFileId, setActiveFileId] = useState<string | null>(null);
  const [view, setView] = useState<'2d' | '3d'>('2d');
  const { upload, isUploading, progress } = useFileUpload();

  useEffect(() => {
    if (!projectId) return;
    void filesApi.listForProject(projectId).then((data) => {
      setFiles(data);
      if (data.length > 0) setActiveFileId((current) => current ?? data[0]?.id ?? null);
    });
  }, [projectId]);

  async function handleUpload(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    if (!file || !projectId) return;
    const created = await upload(file, projectId);
    setFiles((current) => [created, ...(current ?? [])]);
    setActiveFileId(created.id);
    event.target.value = '';
  }

  return (
    <DashboardLayout>
      <div className="space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h1 className="text-2xl font-semibold text-slate-900">CAD editor</h1>
            <p className="text-sm text-slate-600">
              {activeFileId ? 'Real-time collaborative sketch canvas.' : 'Upload a design file to start editing.'}
            </p>
          </div>
          <div className="flex gap-2">
            <button
              type="button"
              onClick={() => setView('2d')}
              className={`rounded-md border px-3 py-2 text-sm ${view === '2d' ? 'border-brand-600 bg-brand-50 text-brand-700' : 'border-slate-300 bg-white text-slate-700'}`}
            >
              2D Sketch
            </button>
            <button
              type="button"
              onClick={() => setView('3d')}
              className={`rounded-md border px-3 py-2 text-sm ${view === '3d' ? 'border-brand-600 bg-brand-50 text-brand-700' : 'border-slate-300 bg-white text-slate-700'}`}
            >
              3D Viewport
            </button>
          </div>
        </div>

        <Card>
          {!activeFileId ? (
            <div className="flex flex-col items-center gap-3 py-10 text-center">
              <p className="text-sm text-slate-600">
                This project doesn&apos;t have any files yet — upload one to start a collaborative session.
              </p>
              <label>
                <input type="file" className="hidden" onChange={handleUpload} disabled={isUploading} />
                <span className="inline-flex cursor-pointer items-center rounded-md bg-brand-600 px-4 py-2 text-sm font-medium text-white">
                  {isUploading ? `Uploading… ${progress}%` : 'Upload a file'}
                </span>
              </label>
            </div>
          ) : view === '2d' ? (
            // key forces a remount (and a fresh Yjs doc) when switching files —
            // useYjsEditor's internal Y.Doc isn't keyed off fileId itself.
            <Canvas2D key={activeFileId} fileId={activeFileId} />
          ) : (
            <Viewport3D bodies={[]} />
          )}
        </Card>

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

export default function CADEditorPage() {
  return (
    <ProtectedRoute>
      <CADEditorPageContent />
    </ProtectedRoute>
  );
}
