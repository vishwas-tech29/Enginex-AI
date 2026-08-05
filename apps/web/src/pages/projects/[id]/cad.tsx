import dynamic from 'next/dynamic';
import { useRouter } from 'next/router';
import { ChangeEvent, useEffect, useState } from 'react';

import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { Card } from '@/components/common/Card';
import { DashboardLayout } from '@/components/layout/DashboardLayout';
import { useFileUpload } from '@/modules/projects/hooks/useFileUpload';
import { Viewport3D } from '@/modules/cad-editor/components/Viewport3D';
import { cadApi, CADObject } from '@/services/api/cad';
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

  const [bodies, setBodies] = useState<CADObject[]>([]);
  const [activeBodyId, setActiveBodyId] = useState<string | null>(null);
  const [isBuilding, setIsBuilding] = useState(false);
  const [buildError, setBuildError] = useState<string | null>(null);
  const [boxSize, setBoxSize] = useState(10);

  useEffect(() => {
    if (!projectId) return;
    void filesApi.listForProject(projectId).then((data) => {
      setFiles(data);
      if (data.length > 0) setActiveFileId((current) => current ?? data[0]?.id ?? null);
    });
  }, [projectId]);

  useEffect(() => {
    if (!activeFileId) {
      setBodies([]);
      setActiveBodyId(null);
      return;
    }
    void cadApi.listBodies(activeFileId).then((data) => {
      setBodies(data);
      setActiveBodyId((current) => current ?? data[0]?.id ?? null);
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

  async function handleQuickBox() {
    if (!activeFileId) return;
    setIsBuilding(true);
    setBuildError(null);
    try {
      // A minimal, real, end-to-end demo of the parametric pipeline: a
      // sketch built from real point/line entities, extruded into a real
      // solid by the CadQuery/OpenCascade kernel — see
      // services/backend/app/cad/. Wiring a full interactive sketcher onto
      // Canvas2D's freeform drawing is a separate follow-up.
      const s = boxSize;
      const sketch = await cadApi.createSketch(activeFileId, `Box ${s}mm sketch`);
      const p0 = await cadApi.addPoint(sketch.id, 0, 0);
      const p1 = await cadApi.addPoint(sketch.id, s, 0);
      const p2 = await cadApi.addPoint(sketch.id, s, s);
      const p3 = await cadApi.addPoint(sketch.id, 0, s);
      await cadApi.addLine(sketch.id, p0.id, p1.id);
      await cadApi.addLine(sketch.id, p1.id, p2.id);
      await cadApi.addLine(sketch.id, p2.id, p3.id);
      await cadApi.addLine(sketch.id, p3.id, p0.id);

      const body = await cadApi.createBody(activeFileId, `Box ${s}mm`);
      await cadApi.extrude(body.id, sketch.id, s);

      const updatedBodies = await cadApi.listBodies(activeFileId);
      setBodies(updatedBodies);
      setActiveBodyId(body.id);
      setView('3d');
    } catch (err) {
      setBuildError(err instanceof Error ? err.message : 'Failed to build solid');
    } finally {
      setIsBuilding(false);
    }
  }

  const activeBody = bodies.find((b) => b.id === activeBodyId) ?? null;

  return (
    <DashboardLayout>
      <div className="space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h1 className="text-2xl font-semibold text-slate-900">CAD editor</h1>
            <p className="text-sm text-slate-600">
              {activeFileId ? 'Real-time collaborative sketch canvas and parametric solid modeling.' : 'Upload a design file to start editing.'}
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
            <Viewport3D bodyId={activeBodyId} />
          )}
        </Card>

        {activeFileId && (
          <Card>
            <div className="flex flex-wrap items-end gap-3">
              <div>
                <h2 className="text-sm font-semibold text-slate-900">Solid bodies</h2>
                <p className="text-xs text-slate-500">Real parametric solids from the CadQuery/OpenCascade kernel.</p>
              </div>
              <div className="ml-auto flex flex-wrap items-end gap-2">
                <label className="text-xs text-slate-600">
                  Box size (mm)
                  <input
                    type="number"
                    min={1}
                    value={boxSize}
                    onChange={(event) => setBoxSize(Number(event.target.value) || 1)}
                    className="mt-1 block w-20 rounded-md border border-slate-300 px-2 py-1 text-sm"
                  />
                </label>
                <button
                  type="button"
                  onClick={handleQuickBox}
                  disabled={isBuilding}
                  className="rounded-md bg-brand-600 px-3 py-2 text-sm font-medium text-white disabled:opacity-60"
                >
                  {isBuilding ? 'Building…' : '+ Quick cube'}
                </button>
              </div>
            </div>

            {buildError && <p className="mt-2 text-sm text-red-600">{buildError}</p>}

            {bodies.length > 0 && (
              <div className="mt-4 flex flex-wrap gap-2">
                {bodies.map((body) => (
                  <button
                    key={body.id}
                    type="button"
                    onClick={() => {
                      setActiveBodyId(body.id);
                      setView('3d');
                    }}
                    className={`rounded-md border px-3 py-1.5 text-sm ${
                      body.id === activeBodyId
                        ? 'border-brand-600 bg-brand-50 text-brand-700'
                        : 'border-slate-200 bg-white text-slate-600'
                    }`}
                  >
                    {body.name}
                  </button>
                ))}
              </div>
            )}

            {activeBody && (
              <div className="mt-3 flex flex-wrap gap-2">
                {(['step', 'stl', 'obj'] as const).map((format) => (
                  <button
                    key={format}
                    type="button"
                    onClick={() => cadApi.downloadExport(activeBody.id, activeBody.name, format)}
                    className="rounded-md border border-slate-300 bg-white px-3 py-1.5 text-xs font-medium text-slate-700 hover:bg-slate-50"
                  >
                    Export {format.toUpperCase()}
                  </button>
                ))}
              </div>
            )}
          </Card>
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

export default function CADEditorPage() {
  return (
    <ProtectedRoute>
      <CADEditorPageContent />
    </ProtectedRoute>
  );
}
