import { getJson } from '$lib/server/api';
import type { MeetingListItem } from '$lib/types/meeting';
import type { PageServerLoad } from './$types';

export const load: PageServerLoad = async ({ cookies, fetch }) => {
	const meetings = await getJson<MeetingListItem[]>(fetch, cookies.get('session'), '/meetings', []);
	return { meetings: meetings.filter((m) => m.me.role === 'invitee') };
};
