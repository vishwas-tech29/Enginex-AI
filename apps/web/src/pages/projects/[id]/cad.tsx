import { useRouter } from 'next/router';

import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { Card } from '@/components/common/Card';
import { DashboardLayout } from '@/components/layout/DashboardLayout';
import { useEditorStore } from '@/store/editorStore';

function CADEditorPageContent() {
  const router = useRouter();
  const { id } = router.query;
  const { selectedObjectIds, zoom, pan, selectObjects, setZoom } = useEditorStore();

  return (
    <DashboardLayout>
      <div className="space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h1 className="text-2xl font-semibold text-slate-900">CAD editor</h1>
            <p className="text-sm text-slate-600">Project {typeof id === 'string' ? id : 'workspace'} is ready for modeling.</p>
          </div>
          <div className="flex gap-2">
            <button type="button" onClick={() => setZoom(zoom + 0.1)} className="rounded-md border border-slate-300 bg-white px-3 py-2 text-sm">
              Zoom +
            </button>
            <button type="button" onClick={() => setZoom(1)} className="rounded-md border border-slate-300 bg-white px-3 py-2 text-sm">
              Reset
            </button>
          </div>
        </div>
        <Card className="min-h-[420px] bg-slate-50">
          <div className="flex items-center justify-between text-sm text-slate-500">
            <span>Zoom: {zoom.toFixed(1)}x</span>
            <span>Pan: {pan.x}, {pan.y}</span>
          </div>
          <div className="mt-4 rounded-xl border border-dashed border-slate-300 bg-white p-10 text-center">
            <p className="text-lg font-semibold text-slate-900">Interactive canvas placeholder</p>
            <p className="mt-2 text-sm text-slate-600">The editor shell is wired for future geometry tools and live collaboration.</p>
            <button
              type="button"
              onClick={() => selectObjects(['part-1', 'part-2'])}
              className="mt-4 rounded-md bg-brand-600 px-4 py-2 text-sm font-medium text-white"
            >
              Select sample parts ({selectedObjectIds.length})
            </button>
          </div>
        </Card>
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
