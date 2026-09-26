import { redirect } from '@sveltejs/kit';
import { API_BASE } from '$lib/server/api';
import type { LayoutServerLoad } from './$types';

export const load: LayoutServerLoad = async ({ locals, cookies, fetch }) => {
	if (locals.user) {
		redirect(303, '/dashboard');
	}

	cookies.delete('session', { path: '/' });

	// Fresh install, no accounts yet — send straight to creating the first administrator.
	const res = await fetch(`${API_BASE}/auth/has-user`);
	const data: { exists: boolean } | null = res.ok ? await res.json() : null;
	if (data && !data.exists) {
		redirect(303, '/register');
	}
};
