import Link from 'next/link';

const NAV_ITEMS = [
  { href: '/dashboard', label: 'Overview' },
  { href: '/dashboard/projects', label: 'Projects' },
  { href: '/dashboard/settings', label: 'Settings' },
];

export function Sidebar() {
  return (
    <aside className="w-56 shrink-0 border-r border-slate-200 bg-white p-4">
      <nav className="flex flex-col gap-1">
        {NAV_ITEMS.map((item) => (
          <Link
            key={item.href}
            href={item.href}
            className="rounded-md px-3 py-2 text-sm text-slate-700 hover:bg-slate-100"
          >
            {item.label}
          </Link>
        ))}
      </nav>
    </aside>
  );
}
