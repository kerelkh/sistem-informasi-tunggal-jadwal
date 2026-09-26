import { error, redirect } from '@sveltejs/kit';
import { API_BASE, authHeaders, getJson } from '$lib/server/api';
import type { Meeting } from '$lib/types/meeting';
import type { PageServerLoad } from './$types';

export const load: PageServerLoad = async ({ params, cookies, fetch }) => {
	const token = cookies.get('session');

	const [meetingRes, categories, invitingUnits] = await Promise.all([
		fetch(`${API_BASE}/meetings/${params.id}`, { headers: authHeaders(token) }),
		getJson<string[]>(fetch, token, '/meetings/meta/categories', []),
		getJson<string[]>(fetch, token, '/meetings/meta/units', [])
	]);

	if (!meetingRes.ok) {
		error(404, 'Rapat tidak ditemukan');
	}

	const meeting: Meeting = await meetingRes.json();
	// Only the organizer edits; everyone else just reads it.
	if (meeting.me.role !== 'organizer') {
		redirect(303, `/dashboard/meetings/${meeting.id}`);
	}

	return { meeting, categories, invitingUnits };
};
