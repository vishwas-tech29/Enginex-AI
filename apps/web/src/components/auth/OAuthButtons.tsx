import { useOAuthLogin } from '@/hooks/useOAuthLogin';

export function OAuthButtons() {
  const { startOAuth } = useOAuthLogin();

  return (
    <div className="flex flex-col gap-2">
      <button
        type="button"
        onClick={() => startOAuth('google')}
        className="flex items-center justify-center gap-2 rounded-md border border-slate-300 bg-white px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50"
      >
        Continue with Google
      </button>
      <button
        type="button"
        onClick={() => startOAuth('github')}
        className="flex items-center justify-center gap-2 rounded-md border border-slate-300 bg-white px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50"
      >
        Continue with GitHub
      </button>
      <div className="my-1 flex items-center gap-3 text-xs text-slate-400">
        <span className="h-px flex-1 bg-slate-200" />
        or
        <span className="h-px flex-1 bg-slate-200" />
      </div>
    </div>
  );
}
