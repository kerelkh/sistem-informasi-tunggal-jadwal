import { redirect } from '@sveltejs/kit';
import { API_BASE } from '$lib/server/api';
import type { LayoutServerLoad } from './$types';

// Setup only exists until the first administrator does.
export const load: LayoutServerLoad = async ({ fetch }) => {
	const res = await fetch(`${API_BASE}/auth/has-user`);
	const data: { exists: boolean } | null = res.ok ? await res.json() : null;
	if (!data || data.exists) {
		redirect(303, '/login');
	}
};
