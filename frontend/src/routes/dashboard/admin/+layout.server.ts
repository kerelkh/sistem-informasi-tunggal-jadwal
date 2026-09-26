import { redirect } from '@sveltejs/kit';
import type { LayoutServerLoad } from './$types';

// The backend refuses admin calls from anyone else; this just avoids a page of errors.
export const load: LayoutServerLoad = async ({ parent }) => {
	const { user } = await parent();
	if (user.role !== 'admin') {
		redirect(303, '/dashboard');
	}
};
