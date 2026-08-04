import { ERCViolation } from '@/services/api/pcb';

export function ERCPanel({ violations }: { violations: ERCViolation[] }) {
  if (violations.length === 0) {
    return <p className="text-xs text-emerald-600">No ERC violations.</p>;
  }

  return (
    <ul className="space-y-1">
      {violations.map((v) => (
        <li
          key={v.id}
          className={`rounded-md border p-2 text-xs ${
            v.severity === 'error' ? 'border-red-200 bg-red-50 text-red-700' : 'border-amber-200 bg-amber-50 text-amber-700'
          }`}
        >
          <div className="font-medium">
            {v.rule} {v.net && <span className="font-normal text-slate-500">· {v.net}</span>}
          </div>
          <div>{v.message}</div>
        </li>
      ))}
    </ul>
  );
}
