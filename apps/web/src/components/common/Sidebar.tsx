import Link from 'next/link';
import { useRouter } from 'next/router';

const NAV_ITEMS = [
  { href: '/dashboard', label: 'Overview' },
  { href: '/dashboard/projects', label: 'Projects' },
  { href: '/dashboard/ai', label: 'AI Workspace' },
  { href: '/dashboard/settings', label: 'Settings' },
];

export function Sidebar() {
  const router = useRouter();

  return (
    <aside className="w-56 shrink-0 border-r border-slate-200 bg-slate-50 p-4">
      <div className="mb-4 rounded-lg border border-slate-200 bg-white p-3 text-sm text-slate-600">
        Design cockpit
      </div>
      <nav className="flex flex-col gap-1">
        {NAV_ITEMS.map((item) => {
          const isActive = router.pathname === item.href || router.pathname.startsWith(`${item.href}/`);
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`rounded-md px-3 py-2 text-sm transition ${
                isActive ? 'bg-brand-50 text-brand-700' : 'text-slate-700 hover:bg-slate-100'
              }`}
            >
              {item.label}
            </Link>
          );
        })}
      </nav>
    </aside>
  );
}
