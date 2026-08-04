import { useRouter } from 'next/router';
import { useCallback, useEffect, useRef } from 'react';

import { useAuth } from '@/hooks/useAuth';
import { authApi, OAuthProvider } from '@/services/api/auth';
import { TokenResponse } from '@/types/api';

const POPUP_WIDTH = 480;
const POPUP_HEIGHT = 640;

export function useOAuthLogin() {
  const router = useRouter();
  const { loginWithOAuthTokens } = useAuth();
  const popupRef = useRef<Window | null>(null);

  useEffect(() => {
    function handleMessage(event: MessageEvent) {
      // The popup navigates to (and the message is sent from) a backend
      // page, not the frontend origin — this must match that, not our own.
      const backendOrigin = new URL(authApi.oauthAuthorizeUrl('google')).origin;
      if (event.origin !== backendOrigin) return;
      if (!event.data || event.data.type !== 'oauth_success') return;

      loginWithOAuthTokens(event.data as TokenResponse);
      popupRef.current?.close();
      void router.push('/dashboard');
    }

    window.addEventListener('message', handleMessage);
    return () => window.removeEventListener('message', handleMessage);
  }, [loginWithOAuthTokens, router]);

  const startOAuth = useCallback((provider: OAuthProvider) => {
    const left = window.screenX + (window.outerWidth - POPUP_WIDTH) / 2;
    const top = window.screenY + (window.outerHeight - POPUP_HEIGHT) / 2;
    popupRef.current = window.open(
      authApi.oauthAuthorizeUrl(provider),
      'oauth-popup',
      `width=${POPUP_WIDTH},height=${POPUP_HEIGHT},left=${left},top=${top}`,
    );
  }, []);

  return { startOAuth };
}
