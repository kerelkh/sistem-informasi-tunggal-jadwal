import { API_BASE, authHeaders } from '$lib/server/api';
import type { RequestHandler } from './$types';

/**
 * Forwards browser calls to the backend with the session token attached. The token
 * lives in an httpOnly cookie, so the browser can't send it itself — this is the only
 * way client code reaches the API. The backend does all the authorisation.
 */
const proxy: RequestHandler = async ({ params, url, request, cookies, fetch }) => {
	const hasBody = request.method !== 'GET' && request.method !== 'DELETE';
	const body = hasBody ? await request.text() : undefined;

	const res = await fetch(`${API_BASE}/${params.path}${url.search}`, {
		method: request.method,
		headers: {
			...authHeaders(cookies.get('session')),
			...(body ? { 'Content-Type': 'application/json' } : {})
		},
		body: body || undefined
	});

	return new Response(res.status === 204 ? null : await res.text(), {
		status: res.status,
		headers: { 'Content-Type': res.headers.get('Content-Type') ?? 'application/json' }
	});
};

export const GET = proxy;
export const POST = proxy;
export const PUT = proxy;
export const PATCH = proxy;
export const DELETE = proxy;
