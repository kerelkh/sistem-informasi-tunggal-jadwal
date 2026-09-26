import { env } from '$env/dynamic/private';
import type { CurrentUser } from '$lib/types/user';

export const API_BASE = env.API_BASE || 'http://localhost:4000/api/v1';

export function authHeaders(token: string | undefined): Record<string, string> {
	return token ? { Authorization: `Bearer ${token}` } : {};
}

/** GETs a JSON resource, falling back when the backend says no rather than throwing. */
export async function getJson<T>(
	fetch: typeof globalThis.fetch,
	token: string | undefined,
	path: string,
	fallback: T
): Promise<T> {
	const res = await fetch(`${API_BASE}${path}`, { headers: authHeaders(token) });
	return res.ok ? res.json() : fallback;
}

/**
 * Verifies the session token against the backend (signature + expiry + user still exists/active),
 * not just whether a cookie happens to be present.
 */
export async function getCurrentUser(
	token: string | undefined,
	fetch: typeof globalThis.fetch
): Promise<CurrentUser | null> {
	if (!token) return null;
	const res = await fetch(`${API_BASE}/auth/me`, { headers: authHeaders(token) });
	if (!res.ok) return null;
	return res.json();
}
