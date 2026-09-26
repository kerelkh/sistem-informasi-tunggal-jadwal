import { getCurrentUser } from '$lib/server/api';
import type { Handle } from '@sveltejs/kit';

export const handle: Handle = async ({ event, resolve }) => {
	// The /api proxy forwards the token and lets the backend judge it, so resolving the
	// user there would only add a round trip. Pages need to know who is looking.
	event.locals.user = event.url.pathname.startsWith('/api/')
		? null
		: await getCurrentUser(event.cookies.get('session'), event.fetch);

	return resolve(event);
};
