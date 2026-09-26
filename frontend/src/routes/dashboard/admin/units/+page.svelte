<script lang="ts">
	import { invalidateAll } from '$app/navigation';
	import * as AlertDialog from '$lib/components/ui/alert-dialog/index.js';
	import * as Dialog from '$lib/components/ui/dialog/index.js';
	import * as Table from '$lib/components/ui/table/index.js';
	import { Button } from '$lib/components/ui/button/index.js';
	import { Input } from '$lib/components/ui/input/index.js';
	import { Label } from '$lib/components/ui/label/index.js';
	import { Textarea } from '$lib/components/ui/textarea/index.js';
	import SiteHeader from '$lib/components/site-header.svelte';
	import type { Unit } from '$lib/types/user';
	import { errorMessage } from '$lib/utils/http';
	import type { PageProps } from './$types';

	let { data }: PageProps = $props();

	let editing = $state<Unit | 'new' | null>(null);
	let name = $state('');
	let code = $state('');
	let description = $state('');
	let saving = $state(false);
	let error = $state('');

	let deleting = $state<Unit | null>(null);
	let deleteError = $state('');

	function open(unit: Unit | 'new') {
		editing = unit;
		name = unit === 'new' ? '' : unit.name;
		code = unit === 'new' ? '' : (unit.code ?? '');
		description = unit === 'new' ? '' : (unit.description ?? '');
		error = '';
	}

	async function save() {
		if (!name.trim()) {
			error = 'Nama wajib diisi.';
			return;
		}
		saving = true;
		const isNew = editing === 'new';
		const res = await fetch(isNew ? '/api/units' : `/api/units/${(editing as Unit).id}`, {
			method: isNew ? 'POST' : 'PUT',
			headers: { 'Content-Type': 'application/json' },
			body: JSON.stringify({
				name: name.trim(),
				code: code.trim() || null,
				description: description.trim() || null
			})
		});
		saving = false;
		if (!res.ok) {
			error = await errorMessage(res);
			return;
		}
		editing = null;
		await invalidateAll();
	}

	async function confirmDelete() {
		if (!deleting) return;
		const res = await fetch(`/api/units/${deleting.id}`, { method: 'DELETE' });
		if (!res.ok) {
			deleteError = await errorMessage(res);
			return;
		}
		deleting = null;
		await invalidateAll();
	}
</script>

<svelte:head>
	<title>Unit Kerja — SITUNG</title>
</svelte:head>

<SiteHeader title="Unit Kerja" />
<div class="flex flex-1 flex-col gap-4 p-4 md:p-6">
	<div class="flex flex-wrap items-center justify-between gap-3">
		<div>
			<h2 class="font-heading text-lg font-semibold">Unit kerja</h2>
			<p class="text-sm text-muted-foreground">
				Unit organisasi tempat pegawai bernaung. Setiap pengguna biasa wajib terdaftar di salah satunya.
			</p>
		</div>
		<Button onclick={() => open('new')}>Unit kerja baru</Button>
	</div>

	{#if data.units.length === 0}
		<div class="rounded-xl border border-dashed py-10 text-center text-muted-foreground">
			Belum ada unit kerja. Buat yang pertama, lalu tambahkan pengguna ke dalamnya.
		</div>
	{:else}
		<div class="rounded-xl border">
			<Table.Root>
				<Table.Header>
					<Table.Row>
						<Table.Head>Nama</Table.Head>
						<Table.Head>Kode</Table.Head>
						<Table.Head>Anggota</Table.Head>
						<Table.Head class="w-0"></Table.Head>
					</Table.Row>
				</Table.Header>
				<Table.Body>
					{#each data.units as u (u.id)}
						<Table.Row>
							<Table.Cell class="whitespace-normal">
								<p class="font-medium">{u.name}</p>
								{#if u.description}
									<p class="text-xs text-muted-foreground">{u.description}</p>
								{/if}
							</Table.Cell>
							<Table.Cell class="text-muted-foreground">{u.code ?? '—'}</Table.Cell>
							<Table.Cell>
								<a href="/dashboard/admin/users?unit={u.id}" class="hover:underline">
									{u.member_count} anggota
								</a>
							</Table.Cell>
							<Table.Cell>
								<div class="flex justify-end gap-1">
									<Button variant="ghost" size="sm" onclick={() => open(u)}>Ubah</Button>
									<Button
										variant="ghost"
										size="sm"
										class="text-destructive hover:text-destructive"
										onclick={() => {
											deleting = u;
											deleteError = '';
										}}
									>
										Hapus
									</Button>
								</div>
							</Table.Cell>
						</Table.Row>
					{/each}
				</Table.Body>
			</Table.Root>
		</div>
	{/if}
</div>

<Dialog.Root open={editing !== null} onOpenChange={(o) => !o && (editing = null)}>
	<Dialog.Content>
		<Dialog.Header>
			<Dialog.Title>{editing === 'new' ? 'Unit kerja baru' : 'Ubah unit kerja'}</Dialog.Title>
		</Dialog.Header>
		<div class="flex flex-col gap-4">
			<div class="flex flex-col gap-1.5">
				<Label for="unit-name">Nama</Label>
				<Input id="unit-name" bind:value={name} placeholder="Biro Umum" />
			</div>
			<div class="flex flex-col gap-1.5">
				<Label for="unit-code">Kode (opsional)</Label>
				<Input id="unit-code" bind:value={code} placeholder="BU" />
			</div>
			<div class="flex flex-col gap-1.5">
				<Label for="unit-desc">Keterangan (opsional)</Label>
				<Textarea id="unit-desc" bind:value={description} />
			</div>
			{#if error}
				<p class="text-sm text-destructive">{error}</p>
			{/if}
		</div>
		<Dialog.Footer>
			<Button variant="outline" onclick={() => (editing = null)}>Batal</Button>
			<Button onclick={save} disabled={saving}>{saving ? 'Menyimpan...' : 'Simpan'}</Button>
		</Dialog.Footer>
	</Dialog.Content>
</Dialog.Root>

<AlertDialog.Root open={deleting !== null} onOpenChange={(o) => !o && (deleting = null)}>
	<AlertDialog.Content>
		<AlertDialog.Header>
			<AlertDialog.Title>Hapus {deleting?.name}?</AlertDialog.Title>
			<AlertDialog.Description>
				Hanya unit kerja tanpa anggota yang dapat dihapus.
			</AlertDialog.Description>
		</AlertDialog.Header>
		{#if deleteError}
			<p class="text-sm text-destructive">{deleteError}</p>
		{/if}
		<AlertDialog.Footer>
			<AlertDialog.Cancel>Tidak jadi</AlertDialog.Cancel>
			<Button variant="destructive" onclick={confirmDelete}>Hapus</Button>
		</AlertDialog.Footer>
	</AlertDialog.Content>
</AlertDialog.Root>
