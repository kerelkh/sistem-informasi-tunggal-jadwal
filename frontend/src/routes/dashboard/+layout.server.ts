import { redirect } from '@sveltejs/kit';
import { getJson } from '$lib/server/api';
import type { Notification } from '$lib/types/notification';
import type { LayoutServerLoad } from './$types';

export const load: LayoutServerLoad = async ({ locals, cookies, fetch }) => {
	const user = locals.user;
	if (!user) {
		cookies.delete('session', { path: '/' });
		redirect(303, '/login');
	}

	const token = cookies.get('session');
	const [notifications, unread, pending] = await Promise.all([
		getJson<Notification[]>(fetch, token, '/notifications', []),
		getJson(fetch, token, '/notifications/unread-count', { count: 0 }),
		getJson(fetch, token, '/meetings/meta/pending-count', { count: 0 })
	]);

	return {
		user,
		notifications,
		unreadNotifications: unread.count,
		pendingInvitations: pending.count
	};
};
