import { getJson } from '$lib/server/api';
import type { MeetingListItem } from '$lib/types/meeting';
import type { PageServerLoad } from './$types';

// Deliberately doesn't read the URL: moving between months/weeks only changes the
// search params, and this way SvelteKit doesn't refetch every meeting on each click.
export const load: PageServerLoad = ({ cookies, fetch }) => {
	return {
		meetings: getJson<MeetingListItem[]>(fetch, cookies.get('session'), '/meetings', [])
	};
};
