import { getJson } from '$lib/server/api';
import type { Unit, UserRecord } from '$lib/types/user';
import type { PageServerLoad } from './$types';

export const load: PageServerLoad = async ({ cookies, fetch }) => {
	const token = cookies.get('session');
	const [users, units] = await Promise.all([
		getJson<UserRecord[]>(fetch, token, '/users', []),
		getJson<Unit[]>(fetch, token, '/units', [])
	]);
	return { users, units };
};
