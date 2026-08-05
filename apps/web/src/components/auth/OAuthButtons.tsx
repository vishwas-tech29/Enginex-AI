import { useOAuthLogin } from '@/hooks/useOAuthLogin';

export function OAuthButtons() {
  const { startOAuth } = useOAuthLogin();

  return (
    <div className="mb-4 flex flex-col gap-2">
      <button
        type="button"
        onClick={() => startOAuth('google')}
        className="flex items-center justify-center gap-2 rounded-xl border border-white/15 bg-white/5 px-3 py-2.5 text-sm font-medium text-white/90 transition-colors hover:bg-white/10"
      >
        Continue with Google
      </button>
      <button
        type="button"
        onClick={() => startOAuth('github')}
        className="flex items-center justify-center gap-2 rounded-xl border border-white/15 bg-white/5 px-3 py-2.5 text-sm font-medium text-white/90 transition-colors hover:bg-white/10"
      >
        Continue with GitHub
      </button>
      <div className="my-1 flex items-center gap-3 text-xs text-white/30">
        <span className="h-px flex-1 bg-white/10" />
        or
        <span className="h-px flex-1 bg-white/10" />
      </div>
    </div>
  );
}
