import { fail, redirect } from '@sveltejs/kit';
import { API_BASE } from '$lib/server/api';
import type { Actions } from './$types';

export const actions: Actions = {
	default: async ({ request, cookies, fetch }) => {
		const data = await request.formData();
		const email = data.get('email');
		const password = data.get('password');

		if (typeof email !== 'string' || typeof password !== 'string' || !email || !password) {
			return fail(400, { error: 'Email dan kata sandi wajib diisi.', email: String(email ?? '') });
		}

		const res = await fetch(`${API_BASE}/auth/login`, {
			method: 'POST',
			headers: { 'Content-Type': 'application/json' },
			body: JSON.stringify({ email, password })
		});

		if (res.status === 429) {
			return fail(429, { error: 'Terlalu banyak percobaan. Tunggu satu menit lalu coba lagi.', email });
		}

		if (res.status === 403) {
			return fail(403, { error: 'Akun ini telah dinonaktifkan. Hubungi administrator.', email });
		}

		if (!res.ok) {
			return fail(401, { error: 'Email atau kata sandi salah.', email });
		}

		const { access_token } = (await res.json()) as { access_token: string };

		cookies.set('session', access_token, {
			path: '/',
			httpOnly: true,
			sameSite: 'lax',
			maxAge: 60 * 60 * 24
		});

		redirect(303, '/dashboard');
	}
};
