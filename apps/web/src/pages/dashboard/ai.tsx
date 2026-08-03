import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { Card } from '@/components/common/Card';
import { DashboardLayout } from '@/components/layout/DashboardLayout';

function AIPageContent() {
  return (
    <DashboardLayout>
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-semibold text-slate-900">AI workspace</h1>
          <p className="text-sm text-slate-600">Use guided prompts for design review, optimization, and documentation.</p>
        </div>
        <Card>
          <div className="space-y-3">
            <div className="rounded-lg bg-slate-50 p-4 text-sm text-slate-700">
              <p className="font-medium">Designer assistant</p>
              <p className="mt-1">“Suggest a more manufacturable PCB stack-up for this board.”</p>
            </div>
            <div className="rounded-lg bg-brand-50 p-4 text-sm text-slate-700">
              <p className="font-medium">Engineering copilot</p>
              <p className="mt-1">“Summarize the mechanical constraints from the current project.”</p>
            </div>
          </div>
        </Card>
      </div>
    </DashboardLayout>
  );
}

export default function AIPage() {
  return (
    <ProtectedRoute>
      <AIPageContent />
    </ProtectedRoute>
  );
}
