import { getJson } from '$lib/server/api';
import type { Unit } from '$lib/types/user';
import type { PageServerLoad } from './$types';

export const load: PageServerLoad = async ({ cookies, fetch }) => {
	return { units: await getJson<Unit[]>(fetch, cookies.get('session'), '/units', []) };
};
