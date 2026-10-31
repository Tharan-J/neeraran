/**
 * NEERARAN API Client
 * Wraps all fetch requests with 4s timeout, role headers, error handling,
 * and Demo Safe Mode offline fallback support.
 */

const API_BASE = '/api';

export async function apiFetch<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const role = sessionStorage.getItem('neeraran_role') || 'admin';
  const userId = sessionStorage.getItem('neeraran_user_id') || 'USER-ADMIN-01';
  const isDemoSafe = sessionStorage.getItem('neeraran_demo_safe') === 'true';

  if (isDemoSafe && endpoint.startsWith('/v1/evaluation')) {
    // Demo safe mode cached responses
    try {
      const fallback = await fetch('/fallback/eval_benchmark.json');
      if (fallback.ok) return await fallback.json();
    } catch {}
  }

  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 4500);

  const headers = {
    'Content-Type': 'application/json',
    'X-User-Role': role,
    'X-User-ID': userId,
    ...(options.headers || {}),
  };

  try {
    const url = endpoint.startsWith('http') ? endpoint : `${API_BASE}${endpoint.startsWith('/') ? '' : '/'}${endpoint}`;
    const resp = await fetch(url, {
      ...options,
      headers,
      signal: controller.signal,
    });

    clearTimeout(timeoutId);

    if (!resp.ok) {
      const errorText = await resp.text();
      throw new Error(`API Error ${resp.status}: ${errorText || resp.statusText}`);
    }

    const contentType = resp.headers.get('content-type');
    if (contentType && contentType.includes('application/json')) {
      return await resp.json();
    }
    return (await resp.text()) as unknown as T;
  } catch (err: any) {
    clearTimeout(timeoutId);
    console.warn(`[apiFetch] Request to ${endpoint} failed:`, err.message);
    throw err;
  }
}
