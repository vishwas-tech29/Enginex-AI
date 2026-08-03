const ACCESS_TOKEN_KEY = 'enginex_access_token';
const REFRESH_TOKEN_KEY = 'enginex_refresh_token';

function isBrowser() {
  return typeof window !== 'undefined';
}

export const storage = {
  getAccessToken(): string | null {
    return isBrowser() ? window.localStorage.getItem(ACCESS_TOKEN_KEY) : null;
  },
  getRefreshToken(): string | null {
    return isBrowser() ? window.localStorage.getItem(REFRESH_TOKEN_KEY) : null;
  },
  setTokens(accessToken: string, refreshToken: string): void {
    if (!isBrowser()) return;
    window.localStorage.setItem(ACCESS_TOKEN_KEY, accessToken);
    window.localStorage.setItem(REFRESH_TOKEN_KEY, refreshToken);
  },
  clearTokens(): void {
    if (!isBrowser()) return;
    window.localStorage.removeItem(ACCESS_TOKEN_KEY);
    window.localStorage.removeItem(REFRESH_TOKEN_KEY);
  },
};
