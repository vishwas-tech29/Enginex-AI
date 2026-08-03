import Link from 'next/link';

import { Button } from '@/components/common/Button';
import { AppLayout } from '@/components/layout/AppLayout';

export default function Home() {
  return (
    <AppLayout>
      <section className="mx-auto flex max-w-3xl flex-col items-center gap-6 px-6 py-24 text-center">
        <h1 className="text-4xl font-bold text-slate-900">
          Design, simulate, and ship hardware with Enginex AI
        </h1>
        <p className="text-lg text-slate-600">
          An AI-native platform for CAD, PCB design, and engineering collaboration.
        </p>
        <div className="flex gap-3">
          <Link href="/register">
            <Button>Get started</Button>
          </Link>
          <Link href="/login">
            <Button variant="secondary">Log in</Button>
          </Link>
        </div>
      </section>
    </AppLayout>
  );
}
