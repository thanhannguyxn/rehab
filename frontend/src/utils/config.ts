// When VITE_API_BASE_URL is empty (or unset), all requests go through the Vite
// dev proxy → same-scheme same-origin → cookies work without SameSite issues.
// Set it to a full URL (e.g. http://localhost:8000) only for Docker or production.
const _apiBase: string = import.meta.env.VITE_API_BASE_URL || '';
const _wsBase: string = import.meta.env.VITE_WS_BASE_URL || '';

const trimSlash = (s: string) => s.replace(/\/+$/, '');

export const API_BASE_URL = trimSlash(_apiBase);
export const API_URL = API_BASE_URL ? `${API_BASE_URL}/api` : '/api';
export const STATIC_BASE_URL = API_BASE_URL ? `${API_BASE_URL}/static` : '/static';

// WebSocket base — proxy mode: derive wss:// from the current browser origin
export const WS_BASE_URL = trimSlash(
  _wsBase ||
    (() => {
      if (typeof window === 'undefined') return 'ws://localhost:3000';
      return window.location.origin
        .replace(/^https/, 'wss')
        .replace(/^http(?!s)/, 'ws');
    })(),
);
