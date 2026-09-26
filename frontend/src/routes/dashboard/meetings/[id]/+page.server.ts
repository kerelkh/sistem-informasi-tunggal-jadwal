import { error } from '@sveltejs/kit';
import { API_BASE, authHeaders, getJson } from '$lib/server/api';
import type { Meeting } from '$lib/types/meeting';
import type { Unit } from '$lib/types/user';
import type { PageServerLoad } from './$types';

export const load: PageServerLoad = async ({ params, cookies, fetch }) => {
	const token = cookies.get('session');
	const [res, units] = await Promise.all([
		fetch(`${API_BASE}/meetings/${params.id}`, { headers: authHeaders(token) }),
		getJson<Unit[]>(fetch, token, '/units', [])
	]);

	if (!res.ok) {
		error(404, 'Rapat tidak ditemukan');
	}

	const meeting: Meeting = await res.json();
	return { meeting, units };
};
