import { getJson } from '$lib/server/api';
import type { Unit } from '$lib/types/user';
import type { PageServerLoad } from './$types';

export const load: PageServerLoad = async ({ cookies, fetch }) => {
	const token = cookies.get('session');
	const [categories, invitingUnits, units] = await Promise.all([
		getJson<string[]>(fetch, token, '/meetings/meta/categories', []),
		getJson<string[]>(fetch, token, '/meetings/meta/units', []),
		getJson<Unit[]>(fetch, token, '/units', [])
	]);
	return { categories, invitingUnits, units };
};
