import { redirect } from '@sveltejs/kit';
import type { PageServerLoad } from './$types';

// There's no public site — the app is the dashboard.
export const load: PageServerLoad = ({ locals }) => {
	redirect(303, locals.user ? '/dashboard' : '/login');
};
