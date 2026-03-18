const trimTrailingSlash = (value: string): string => value.replace(/\/+$/, '');

const apiBaseUrlRaw = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
const wsBaseUrlRaw =
  import.meta.env.VITE_WS_BASE_URL ||
  apiBaseUrlRaw.replace(/^http/i, (prefix: string) => (prefix.toLowerCase() === 'https' ? 'wss' : 'ws'));

export const API_BASE_URL = trimTrailingSlash(apiBaseUrlRaw);
export const WS_BASE_URL = trimTrailingSlash(wsBaseUrlRaw);

export const API_URL = `${API_BASE_URL}/api`;
export const STATIC_BASE_URL = `${API_BASE_URL}/static`;
