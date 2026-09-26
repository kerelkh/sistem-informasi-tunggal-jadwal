<script lang="ts">
	import { untrack } from 'svelte';
	import { invalidateAll } from '$app/navigation';
	import * as Card from '$lib/components/ui/card/index.js';
	import { Button } from '$lib/components/ui/button/index.js';
	import { Input } from '$lib/components/ui/input/index.js';
	import { Label } from '$lib/components/ui/label/index.js';
	import SiteHeader from '$lib/components/site-header.svelte';
	import { errorMessage } from '$lib/utils/http';
	import type { PageProps } from './$types';

	let { data }: PageProps = $props();

	// Form fields start from the saved profile and are then the user's to edit.
	let fullName = $state(untrack(() => data.user.full_name ?? ''));
	let email = $state(untrack(() => data.user.email));
	let savingProfile = $state(false);
	let profileMessage = $state<{ ok: boolean; text: string } | null>(null);

	let currentPassword = $state('');
	let newPassword = $state('');
	let confirmPassword = $state('');
	let savingPassword = $state(false);
	let passwordMessage = $state<{ ok: boolean; text: string } | null>(null);

	async function saveProfile() {
		savingProfile = true;
		profileMessage = null;
		const res = await fetch('/api/auth/me', {
			method: 'PUT',
			headers: { 'Content-Type': 'application/json' },
			body: JSON.stringify({ full_name: fullName.trim() || null, email: email.trim() })
		});
		savingProfile = false;
		profileMessage = res.ok
			? { ok: true, text: 'Tersimpan.' }
			: { ok: false, text: await errorMessage(res, 'Tidak dapat menyimpan.') };
		if (res.ok) await invalidateAll();
	}

	async function changePassword() {
		passwordMessage = null;
		if (newPassword.length < 8) {
			passwordMessage = { ok: false, text: 'Kata sandi baru minimal 8 karakter.' };
			return;
		}
		if (newPassword !== confirmPassword) {
			passwordMessage = { ok: false, text: 'Kedua kata sandi baru tidak sama.' };
			return;
		}
		savingPassword = true;
		const res = await fetch('/api/auth/me/change-password', {
			method: 'POST',
			headers: { 'Content-Type': 'application/json' },
			body: JSON.stringify({ current_password: currentPassword, new_password: newPassword })
		});
		savingPassword = false;
		if (res.ok) {
			currentPassword = newPassword = confirmPassword = '';
			passwordMessage = { ok: true, text: 'Kata sandi berhasil diubah.' };
		} else {
			passwordMessage = { ok: false, text: await errorMessage(res, 'Kata sandi tidak dapat diubah.') };
		}
	}
</script>

<svelte:head>
	<title>Pengaturan — SITUNG</title>
</svelte:head>

<SiteHeader title="Pengaturan" />
<div class="flex flex-1 flex-col gap-6 p-4 md:p-6">
	<div class="grid max-w-4xl gap-6 lg:grid-cols-2">
		<Card.Root>
			<Card.Header>
				<Card.Title>Profil</Card.Title>
				<Card.Description>
					Unit kerja, jabatan, dan peran Anda diatur oleh administrator.
				</Card.Description>
			</Card.Header>
			<Card.Content class="flex flex-col gap-4">
				<div class="flex flex-col gap-1.5">
					<Label for="full-name">Nama lengkap</Label>
					<Input id="full-name" bind:value={fullName} />
				</div>
				<div class="flex flex-col gap-1.5">
					<Label for="email">Email</Label>
					<Input id="email" type="email" bind:value={email} />
				</div>
				<dl class="grid grid-cols-2 gap-3 rounded-xl bg-muted/50 p-3 text-sm">
					<div>
						<dt class="text-xs text-muted-foreground">Unit kerja</dt>
						<dd>{data.user.unit?.name ?? '—'}</dd>
					</div>
					<div>
						<dt class="text-xs text-muted-foreground">Jabatan</dt>
						<dd>{data.user.position ?? '—'}</dd>
					</div>
					<div>
						<dt class="text-xs text-muted-foreground">Peran</dt>
						<dd class="capitalize">{data.user.role === 'admin' ? 'Administrator' : 'Pengguna'}</dd>
					</div>
				</dl>
				{#if profileMessage}
					<p class="text-sm {profileMessage.ok ? 'text-muted-foreground' : 'text-destructive'}">
						{profileMessage.text}
					</p>
				{/if}
			</Card.Content>
			<Card.Footer>
				<Button onclick={saveProfile} disabled={savingProfile}>
					{savingProfile ? 'Menyimpan...' : 'Simpan profil'}
				</Button>
			</Card.Footer>
		</Card.Root>

		<Card.Root>
			<Card.Header>
				<Card.Title>Kata sandi</Card.Title>
			</Card.Header>
			<Card.Content class="flex flex-col gap-4">
				<div class="flex flex-col gap-1.5">
					<Label for="current">Kata sandi saat ini</Label>
					<Input id="current" type="password" autocomplete="current-password" bind:value={currentPassword} />
				</div>
				<div class="flex flex-col gap-1.5">
					<Label for="new">Kata sandi baru</Label>
					<Input id="new" type="password" autocomplete="new-password" bind:value={newPassword} />
				</div>
				<div class="flex flex-col gap-1.5">
					<Label for="confirm">Ulangi kata sandi baru</Label>
					<Input id="confirm" type="password" autocomplete="new-password" bind:value={confirmPassword} />
				</div>
				{#if passwordMessage}
					<p class="text-sm {passwordMessage.ok ? 'text-muted-foreground' : 'text-destructive'}">
						{passwordMessage.text}
					</p>
				{/if}
			</Card.Content>
			<Card.Footer>
				<Button onclick={changePassword} disabled={savingPassword || !currentPassword}>
					{savingPassword ? 'Menyimpan...' : 'Ubah kata sandi'}
				</Button>
			</Card.Footer>
		</Card.Root>
	</div>
</div>
