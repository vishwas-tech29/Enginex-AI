const ACCESS_TOKEN_KEY = 'enginex_access_token';
const REFRESH_TOKEN_KEY = 'enginex_refresh_token';
const REMEMBER_ME_KEY = 'enginex_remember_me';

function isBrowser() {
  return typeof window !== 'undefined';
}

function isRemembered(): boolean {
  if (!isBrowser()) return true;
  // Unset (no prior login, or a session predating remember-me) defaults to
  // true — the original always-localStorage behavior, so existing sessions
  // aren't silently downgraded to session-only on the next deploy.
  return window.localStorage.getItem(REMEMBER_ME_KEY) !== 'false';
}

function activeStore(): Storage | null {
  if (!isBrowser()) return null;
  return isRemembered() ? window.localStorage : window.sessionStorage;
}

export const storage = {
  getAccessToken(): string | null {
    return activeStore()?.getItem(ACCESS_TOKEN_KEY) ?? null;
  },
  getRefreshToken(): string | null {
    return activeStore()?.getItem(REFRESH_TOKEN_KEY) ?? null;
  },
  /** rememberMe omitted keeps whatever mode is already active (used when
   * silently rotating tokens on refresh, where the user isn't re-choosing). */
  setTokens(accessToken: string, refreshToken: string, rememberMe?: boolean): void {
    if (!isBrowser()) return;
    const persist = rememberMe ?? isRemembered();
    window.localStorage.setItem(REMEMBER_ME_KEY, String(persist));

    const store = persist ? window.localStorage : window.sessionStorage;
    const other = persist ? window.sessionStorage : window.localStorage;
    other.removeItem(ACCESS_TOKEN_KEY);
    other.removeItem(REFRESH_TOKEN_KEY);
    store.setItem(ACCESS_TOKEN_KEY, accessToken);
    store.setItem(REFRESH_TOKEN_KEY, refreshToken);
  },
  clearTokens(): void {
    if (!isBrowser()) return;
    window.localStorage.removeItem(ACCESS_TOKEN_KEY);
    window.localStorage.removeItem(REFRESH_TOKEN_KEY);
    window.localStorage.removeItem(REMEMBER_ME_KEY);
    window.sessionStorage.removeItem(ACCESS_TOKEN_KEY);
    window.sessionStorage.removeItem(REFRESH_TOKEN_KEY);
  },
};
