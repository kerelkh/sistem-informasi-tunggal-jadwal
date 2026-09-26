import { getJson } from '$lib/server/api';
import type { MeetingListItem } from '$lib/types/meeting';
import type { PageServerLoad } from './$types';

export const load: PageServerLoad = ({ cookies, fetch }) => {
	return {
		meetings: getJson<MeetingListItem[]>(fetch, cookies.get('session'), '/meetings', [])
	};
};
