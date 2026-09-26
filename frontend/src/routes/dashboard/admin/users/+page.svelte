<script lang="ts">
	import { invalidateAll } from '$app/navigation';
	import { page } from '$app/state';
	import * as Dialog from '$lib/components/ui/dialog/index.js';
	import * as Select from '$lib/components/ui/select/index.js';
	import * as Table from '$lib/components/ui/table/index.js';
	import { Badge } from '$lib/components/ui/badge/index.js';
	import { Button } from '$lib/components/ui/button/index.js';
	import { Input } from '$lib/components/ui/input/index.js';
	import { Label } from '$lib/components/ui/label/index.js';
	import { Switch } from '$lib/components/ui/switch/index.js';
	import SiteHeader from '$lib/components/site-header.svelte';
	import { displayName, type UserRecord, type UserRole } from '$lib/types/user';
	import { errorMessage } from '$lib/utils/http';
	import type { PageProps } from './$types';

	let { data }: PageProps = $props();

	let query = $state('');
	let unitFilter = $state(page.url.searchParams.get('unit') ?? 'all');
	const unitName = (id: string) => data.units.find((u) => String(u.id) === id)?.name ?? 'Unit kerja';

	const shown = $derived(
		data.users.filter((u) => {
			if (unitFilter === 'none' && u.unit) return false;
			if (unitFilter !== 'all' && unitFilter !== 'none' && String(u.unit?.id) !== unitFilter) return false;
			const q = query.trim().toLowerCase();
			return (
				!q ||
				[u.full_name, u.email, u.position, u.unit?.name]
					.filter(Boolean)
					.some((f) => f!.toLowerCase().includes(q))
			);
		})
	);

	// --- create / edit ---
	let editing = $state<UserRecord | 'new' | null>(null);
	let form = $state({
		full_name: '',
		email: '',
		position: '',
		password: '',
		role: 'user' as UserRole,
		unit_id: '',
		is_active: true
	});
	let saving = $state(false);
	let error = $state('');

	const isSelf = $derived(editing !== null && editing !== 'new' && editing.id === data.user.id);

	function open(user: UserRecord | 'new') {
		editing = user;
		error = '';
		form =
			user === 'new'
				? {
						full_name: '',
						email: '',
						position: '',
						password: '',
						role: 'user',
						unit_id: unitFilter !== 'all' && unitFilter !== 'none' ? unitFilter : '',
						is_active: true
					}
				: {
						full_name: user.full_name ?? '',
						email: user.email,
						position: user.position ?? '',
						password: '',
						role: user.role,
						unit_id: user.unit ? String(user.unit.id) : '',
						is_active: user.is_active
					};
	}

	async function save() {
		if (!form.full_name.trim() || !form.email.trim()) {
			error = 'Nama dan email wajib diisi.';
			return;
		}
		if (form.role === 'user' && !form.unit_id) {
			error = 'Pengguna biasa wajib terdaftar di sebuah unit kerja.';
			return;
		}
		if (editing === 'new' && form.password.length < 8) {
			error = 'Kata sandi awal minimal 8 karakter.';
			return;
		}

		const body = {
			full_name: form.full_name.trim(),
			email: form.email.trim(),
			position: form.position.trim() || null,
			role: form.role,
			unit_id: form.unit_id ? Number(form.unit_id) : null,
			...(editing === 'new' ? { password: form.password } : { is_active: form.is_active })
		};

		saving = true;
		const res = await fetch(editing === 'new' ? '/api/users' : `/api/users/${(editing as UserRecord).id}`, {
			method: editing === 'new' ? 'POST' : 'PUT',
			headers: { 'Content-Type': 'application/json' },
			body: JSON.stringify(body)
		});
		saving = false;
		if (!res.ok) {
			error = await errorMessage(res);
			return;
		}
		editing = null;
		await invalidateAll();
	}

	// --- reset password ---
	let resetting = $state<UserRecord | null>(null);
	let newPassword = $state('');
	let resetError = $state('');
	let resetDone = $state(false);

	async function resetPassword() {
		if (!resetting) return;
		if (newPassword.length < 8) {
			resetError = 'Minimal 8 karakter.';
			return;
		}
		const res = await fetch(`/api/users/${resetting.id}/reset-password`, {
			method: 'POST',
			headers: { 'Content-Type': 'application/json' },
			body: JSON.stringify({ new_password: newPassword })
		});
		if (!res.ok) {
			resetError = await errorMessage(res);
			return;
		}
		resetDone = true;
	}
</script>

<svelte:head>
	<title>Pengguna — SITUNG</title>
</svelte:head>

<SiteHeader title="Pengguna" />
<div class="flex flex-1 flex-col gap-4 p-4 md:p-6">
	<div class="flex flex-wrap items-center justify-between gap-3">
		<div>
			<h2 class="font-heading text-lg font-semibold">Pengguna</h2>
			<p class="text-sm text-muted-foreground">
				Buat akun, tempatkan pegawai di unit kerja, dan berikan akses administrator.
			</p>
		</div>
		<Button onclick={() => open('new')} disabled={data.units.length === 0}>Pengguna baru</Button>
	</div>

	{#if data.units.length === 0}
		<p class="rounded-xl border border-primary/30 bg-primary/5 p-3 text-sm">
			Buat unit kerja terlebih dahulu — setiap pengguna biasa wajib terdaftar di salah satunya.
			<a href="/dashboard/admin/units" class="font-medium underline">Buka Unit Kerja</a>
		</p>
	{/if}

	<div class="flex flex-wrap items-center gap-2">
		<Input bind:value={query} placeholder="Cari nama, email, jabatan..." class="max-w-xs" />
		<Select.Root type="single" bind:value={unitFilter}>
			<Select.Trigger class="w-52">
				{unitFilter === 'all' ? 'Semua unit kerja' : unitFilter === 'none' ? 'Tanpa unit kerja' : unitName(unitFilter)}
			</Select.Trigger>
			<Select.Content>
				<Select.Item value="all">Semua unit kerja</Select.Item>
				<Select.Item value="none">Tanpa unit kerja</Select.Item>
				{#each data.units as u (u.id)}
					<Select.Item value={String(u.id)}>{u.name}</Select.Item>
				{/each}
			</Select.Content>
		</Select.Root>
		<span class="text-xs text-muted-foreground">{shown.length} dari {data.users.length}</span>
	</div>

	<div class="rounded-xl border">
		<Table.Root>
			<Table.Header>
				<Table.Row>
					<Table.Head>Nama</Table.Head>
					<Table.Head>Unit kerja</Table.Head>
					<Table.Head>Jabatan</Table.Head>
					<Table.Head>Peran</Table.Head>
					<Table.Head>Status</Table.Head>
					<Table.Head class="w-0"></Table.Head>
				</Table.Row>
			</Table.Header>
			<Table.Body>
				{#each shown as u (u.id)}
					<Table.Row class={u.is_active ? '' : 'opacity-60'}>
						<Table.Cell class="whitespace-normal">
							<p class="font-medium">
								{displayName(u)}
								{#if u.id === data.user.id}<span class="text-muted-foreground">(Anda)</span>{/if}
							</p>
							<p class="text-xs text-muted-foreground">{u.email}</p>
						</Table.Cell>
						<Table.Cell class="text-muted-foreground">{u.unit?.name ?? '—'}</Table.Cell>
						<Table.Cell class="text-muted-foreground">{u.position ?? '—'}</Table.Cell>
						<Table.Cell>
							<Badge variant={u.role === 'admin' ? 'default' : 'secondary'}>
								{u.role === 'admin' ? 'Administrator' : 'Pengguna'}
							</Badge>
						</Table.Cell>
						<Table.Cell>
							<Badge variant={u.is_active ? 'outline' : 'destructive'}>
								{u.is_active ? 'Aktif' : 'Nonaktif'}
							</Badge>
						</Table.Cell>
						<Table.Cell>
							<div class="flex justify-end gap-1">
								<Button variant="ghost" size="sm" onclick={() => open(u)}>Ubah</Button>
								<Button
									variant="ghost"
									size="sm"
									onclick={() => {
										resetting = u;
										newPassword = '';
										resetError = '';
										resetDone = false;
									}}
								>
									Atur ulang sandi
								</Button>
							</div>
						</Table.Cell>
					</Table.Row>
				{:else}
					<Table.Row>
						<Table.Cell colspan={6} class="py-8 text-center text-muted-foreground">
							Tidak ada yang cocok.
						</Table.Cell>
					</Table.Row>
				{/each}
			</Table.Body>
		</Table.Root>
	</div>
</div>

<Dialog.Root open={editing !== null} onOpenChange={(o) => !o && (editing = null)}>
	<Dialog.Content>
		<Dialog.Header>
			<Dialog.Title>{editing === 'new' ? 'Pengguna baru' : 'Ubah pengguna'}</Dialog.Title>
			{#if editing === 'new'}
				<Dialog.Description>
					Sampaikan kata sandi awal kepada yang bersangkutan — kata sandi dapat diubah di Pengaturan.
				</Dialog.Description>
			{/if}
		</Dialog.Header>
		<div class="grid gap-4 sm:grid-cols-2">
			<div class="flex flex-col gap-1.5 sm:col-span-2">
				<Label for="u-name">Nama lengkap</Label>
				<Input id="u-name" bind:value={form.full_name} />
			</div>
			<div class="flex flex-col gap-1.5 sm:col-span-2">
				<Label for="u-email">Email</Label>
				<Input id="u-email" type="email" bind:value={form.email} />
			</div>
			<div class="flex flex-col gap-1.5">
				<Label for="u-position">Jabatan</Label>
				<Input id="u-position" bind:value={form.position} placeholder="Kepala Bagian..." />
			</div>
			<div class="flex flex-col gap-1.5">
				<Label>Unit kerja</Label>
				<Select.Root type="single" bind:value={form.unit_id}>
					<Select.Trigger class="w-full">
						{form.unit_id ? unitName(form.unit_id) : 'Tanpa unit kerja'}
					</Select.Trigger>
					<Select.Content>
						<Select.Item value="">Tanpa unit kerja</Select.Item>
						{#each data.units as u (u.id)}
							<Select.Item value={String(u.id)}>{u.name}</Select.Item>
						{/each}
					</Select.Content>
				</Select.Root>
			</div>
			<div class="flex flex-col gap-1.5">
				<Label>Peran</Label>
				<Select.Root type="single" bind:value={form.role} disabled={isSelf}>
					<Select.Trigger class="w-full">
						{form.role === 'admin' ? 'Administrator' : 'Pengguna'}
					</Select.Trigger>
					<Select.Content>
						<Select.Item value="user">Pengguna</Select.Item>
						<Select.Item value="admin">Administrator</Select.Item>
					</Select.Content>
				</Select.Root>
			</div>
			{#if editing === 'new'}
				<div class="flex flex-col gap-1.5">
					<Label for="u-password">Kata sandi awal</Label>
					<Input id="u-password" type="text" autocomplete="off" bind:value={form.password} />
				</div>
			{:else}
				<div class="flex items-center justify-between gap-2 self-end rounded-xl border px-3 py-2">
					<Label for="u-active" class="text-sm font-normal">Aktif</Label>
					<Switch id="u-active" bind:checked={form.is_active} disabled={isSelf} />
				</div>
			{/if}
			{#if isSelf}
				<p class="text-xs text-muted-foreground sm:col-span-2">
					Anda tidak dapat mencabut akses administrator atau menonaktifkan akun Anda sendiri.
				</p>
			{/if}
			{#if error}
				<p class="text-sm text-destructive sm:col-span-2">{error}</p>
			{/if}
		</div>
		<Dialog.Footer>
			<Button variant="outline" onclick={() => (editing = null)}>Batal</Button>
			<Button onclick={save} disabled={saving}>{saving ? 'Menyimpan...' : 'Simpan'}</Button>
		</Dialog.Footer>
	</Dialog.Content>
</Dialog.Root>

<Dialog.Root open={resetting !== null} onOpenChange={(o) => !o && (resetting = null)}>
	<Dialog.Content>
		<Dialog.Header>
			<Dialog.Title>Atur ulang kata sandi</Dialog.Title>
			<Dialog.Description>
				Tetapkan kata sandi baru untuk {resetting ? displayName(resetting) : ''}.
			</Dialog.Description>
		</Dialog.Header>
		{#if resetDone}
			<p class="text-sm">Selesai. Sampaikan kata sandi baru kepada yang bersangkutan.</p>
			<Dialog.Footer>
				<Button onclick={() => (resetting = null)}>Tutup</Button>
			</Dialog.Footer>
		{:else}
			<div class="flex flex-col gap-1.5">
				<Label for="reset-pw">Kata sandi baru</Label>
				<Input id="reset-pw" type="text" autocomplete="off" bind:value={newPassword} />
			</div>
			{#if resetError}
				<p class="text-sm text-destructive">{resetError}</p>
			{/if}
			<Dialog.Footer>
				<Button variant="outline" onclick={() => (resetting = null)}>Batal</Button>
				<Button onclick={resetPassword}>Simpan</Button>
			</Dialog.Footer>
		{/if}
	</Dialog.Content>
</Dialog.Root>
