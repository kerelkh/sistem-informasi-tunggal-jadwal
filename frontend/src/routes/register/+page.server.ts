import { fail, redirect } from '@sveltejs/kit';
import { API_BASE } from '$lib/server/api';
import type { Actions } from './$types';

export const actions: Actions = {
	default: async ({ request, cookies, fetch }) => {
		const data = await request.formData();
		const fullName = String(data.get('full_name') ?? '').trim();
		const email = String(data.get('email') ?? '').trim();
		const password = String(data.get('password') ?? '');
		const confirm = String(data.get('confirm') ?? '');

		if (!fullName || !email || !password) {
			return fail(400, { error: 'Semua kolom wajib diisi.', email, fullName });
		}
		if (password.length < 8) {
			return fail(400, { error: 'Kata sandi minimal 8 karakter.', email, fullName });
		}
		if (password !== confirm) {
			return fail(400, { error: 'Kedua kata sandi tidak sama.', email, fullName });
		}

		const res = await fetch(`${API_BASE}/auth/register`, {
			method: 'POST',
			headers: { 'Content-Type': 'application/json' },
			body: JSON.stringify({ email, password, full_name: fullName })
		});

		if (!res.ok) {
			const body = await res.json().catch(() => null);
			const detail = typeof body?.detail === 'string' ? body.detail : 'Akun tidak dapat dibuat.';
			return fail(res.status, { error: detail, email, fullName });
		}

		const loginRes = await fetch(`${API_BASE}/auth/login`, {
			method: 'POST',
			headers: { 'Content-Type': 'application/json' },
			body: JSON.stringify({ email, password })
		});
		if (!loginRes.ok) redirect(303, '/login');

		const { access_token } = (await loginRes.json()) as { access_token: string };
		cookies.set('session', access_token, {
			path: '/',
			httpOnly: true,
			sameSite: 'lax',
			maxAge: 60 * 60 * 24
		});

		// Nothing works until there's a unit to put people in.
		redirect(303, '/dashboard/admin/units');
	}
};
