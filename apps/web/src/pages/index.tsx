import Link from 'next/link';

import { Button } from '@/components/common/Button';
import { AppLayout } from '@/components/layout/AppLayout';

const highlights = [
  'Realtime CAD and PCB collaboration',
  'AI review and design assistance',
  'Versioned files ready for manufacturing',
];

export default function Home() {
  return (
    <AppLayout>
      <section className="mx-auto flex max-w-6xl flex-col gap-12 px-6 py-20 lg:py-28">
        <div className="grid items-center gap-10 lg:grid-cols-[1.1fr_0.9fr]">
          <div className="max-w-2xl">
            <p className="mb-4 inline-flex rounded-full bg-brand-50 px-3 py-1 text-sm font-medium text-brand-700">
              AI-native hardware design platform
            </p>
            <h1 className="text-4xl font-semibold tracking-tight text-slate-900 sm:text-5xl">
              Move from concept sketches to manufacturing-ready designs in one workspace.
            </h1>
            <p className="mt-6 text-lg text-slate-600">
              Enginex AI brings CAD, PCB, collaboration, and assistant-driven review into a single, elegant surface.
            </p>
            <div className="mt-8 flex flex-wrap gap-3">
              <Link href="/register">
                <Button>Start free</Button>
              </Link>
              <Link href="/login">
                <Button variant="secondary">Log in</Button>
              </Link>
            </div>
          </div>
          <div className="rounded-2xl border border-slate-200 bg-white p-8 shadow-sm">
            <div className="rounded-xl bg-slate-900 p-6 text-white">
              <p className="text-sm text-slate-300">Live design workspace</p>
              <p className="mt-3 text-2xl font-semibold">15+ modeling and review workflows</p>
              <ul className="mt-5 space-y-2 text-sm text-slate-300">
                {highlights.map((item) => (
                  <li key={item}>• {item}</li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      </section>
    </AppLayout>
  );
}
