<script lang="ts">
	import { untrack } from 'svelte';
	import * as Avatar from '$lib/components/ui/avatar/index.js';
	import * as Select from '$lib/components/ui/select/index.js';
	import { Button } from '$lib/components/ui/button/index.js';
	import { Input } from '$lib/components/ui/input/index.js';
	import { Label } from '$lib/components/ui/label/index.js';
	import { Skeleton } from '$lib/components/ui/skeleton/index.js';
	import SiteHeader from '$lib/components/site-header.svelte';
	import AvailabilityStatus from '$lib/components/availability-status.svelte';
	import { fetchAvailability, type AvailabilityResult } from '$lib/types/availability';
	import { addMinutes, nowLocal, zoneLabel } from '$lib/types/meeting';
	import { displayName, initials } from '$lib/types/user';
	import type { PageProps } from './$types';

	let { data }: PageProps = $props();

	// Default window: the next full hour on your own clock, one hour long — "are they free in a bit?"
	const now = nowLocal();
	const nextHour = addMinutes(`${now.slice(0, 13)}:00`, 60);

	let from = $state(nextHour);
	let to = $state(addMinutes(nextHour, 60));
	let query = $state('');
	// Start on the viewer's own unit — "who in my team is free?" is the common question.
	let unitFilter = $state(untrack(() => String(data.user.unit?.id ?? 'all')));
	let onlyAvailable = $state(false);

	let result = $state<AvailabilityResult | null>(null);
	let loading = $state(false);
	let error = $state('');

	const unitLabel = $derived(
		unitFilter === 'all'
			? 'Semua unit kerja'
			: (data.units.find((u) => String(u.id) === unitFilter)?.name ?? 'Unit kerja')
	);

	let seq = 0;
	$effect(() => {
		const args = { from, to, query, unitFilter };
		if (!args.from) {
			result = null;
			return;
		}
		const mine = ++seq;
		loading = true;
		const timer = setTimeout(async () => {
			try {
				const res = await fetchAvailability({
					start: args.from,
					end: args.to || undefined,
					q: args.query,
					unitId: args.unitFilter === 'all' ? null : Number(args.unitFilter)
				});
				if (mine !== seq) return;
				result = res;
				error = '';
			} catch (e) {
				if (mine !== seq) return;
				error = e instanceof Error ? e.message : 'Ketersediaan tidak dapat diperiksa.';
			} finally {
				if (mine === seq) loading = false;
			}
		}, 250);
		return () => clearTimeout(timer);
	});

	const people = $derived(
		(result?.users ?? []).filter((u) => !onlyAvailable || u.available)
	);
	const freeCount = $derived((result?.users ?? []).filter((u) => u.available).length);
</script>

<svelte:head>
	<title>Ketersediaan — SITUNG</title>
</svelte:head>

<SiteHeader title="Ketersediaan" />
<div class="flex flex-1 flex-col gap-4 p-4 md:p-6">
	<div>
		<h2 class="font-heading text-lg font-semibold">Siapa yang tersedia?</h2>
		<p class="text-sm text-muted-foreground">
			Pilih rentang waktu untuk melihat siapa yang jadwalnya kosong. Hanya rapat formal yang sudah
			diterima yang membuat seseorang sibuk; rapat informal dan undangan yang belum dijawab tetap
			ditampilkan tetapi tidak dihitung sibuk. Waktu ditampilkan sesuai zona waktu perangkat Anda ({zoneLabel()}).
		</p>
	</div>

	<div class="flex flex-wrap items-end gap-3 rounded-xl border p-4">
		<div class="flex flex-col gap-1.5">
			<Label for="from" class="text-xs text-muted-foreground">Dari ({zoneLabel()})</Label>
			<Input id="from" type="datetime-local" bind:value={from} class="w-56" />
		</div>
		<div class="flex flex-col gap-1.5">
			<Label for="to" class="text-xs text-muted-foreground">Sampai ({zoneLabel()})</Label>
			<Input id="to" type="datetime-local" bind:value={to} class="w-56" />
		</div>
		<div class="flex flex-col gap-1.5">
			<Label class="text-xs text-muted-foreground">Unit kerja</Label>
			<Select.Root type="single" bind:value={unitFilter}>
				<Select.Trigger class="w-52">{unitLabel}</Select.Trigger>
				<Select.Content>
					<Select.Item value="all">Semua unit kerja</Select.Item>
					{#each data.units as u (u.id)}
						<Select.Item value={String(u.id)}>{u.name}</Select.Item>
					{/each}
				</Select.Content>
			</Select.Root>
		</div>
		<div class="flex min-w-48 flex-1 flex-col gap-1.5">
			<Label for="who" class="text-xs text-muted-foreground">Nama</Label>
			<Input id="who" bind:value={query} placeholder="Nama, email, atau jabatan" />
		</div>
	</div>

	{#if !from}
		<p class="text-sm text-muted-foreground">
			Isi waktu mulai. Kosongkan "Sampai" untuk memeriksa hingga akhir hari tersebut.
		</p>
	{:else if error}
		<p class="text-sm text-destructive">{error}</p>
	{:else if loading && !result}
		<div class="flex flex-col gap-2">
			{#each { length: 4 } as _, i (i)}
				<Skeleton class="h-16 w-full rounded-xl" />
			{/each}
		</div>
	{:else if result}
		<div class="flex flex-wrap items-center justify-between gap-3">
			<p class="text-sm">
				<strong>{freeCount}</strong> dari {result.users.length} tersedia
				{#if result.users.length === 50}
					<span class="text-muted-foreground">(menampilkan 50 pertama — persempit pencarian)</span>
				{/if}
			</p>
			<div class="flex items-center gap-2">
				<Button variant={onlyAvailable ? 'secondary' : 'ghost'} size="sm" onclick={() => (onlyAvailable = !onlyAvailable)}>
					{onlyAvailable ? 'Hanya yang tersedia' : 'Tampilkan yang tersedia saja'}
				</Button>
				<Button
					size="sm"
					href="/dashboard/meetings/new?start={encodeURIComponent(from)}&end={encodeURIComponent(to)}"
				>
					Buat rapat di waktu ini
				</Button>
			</div>
		</div>

		{#if people.length === 0}
			<div class="rounded-xl border border-dashed py-10 text-center text-muted-foreground">
				Tidak ada yang cocok.
			</div>
		{:else}
			<ul class="flex flex-col divide-y rounded-xl border {loading ? 'opacity-60' : ''}">
				{#each people as r (r.user.id)}
					<li class="flex items-start gap-3 p-3">
						<Avatar.Root class="size-9">
							<Avatar.Fallback class="text-xs">{initials(r.user)}</Avatar.Fallback>
						</Avatar.Root>
						<div class="min-w-0 flex-1 sm:flex sm:gap-6">
							<div class="min-w-0 sm:w-64 sm:shrink-0">
								<p class="truncate text-sm font-medium">
									{displayName(r.user)}
									{#if r.user.id === data.user.id}<span class="text-muted-foreground">(Anda)</span>{/if}
								</p>
								<p class="truncate text-xs text-muted-foreground">
									{[r.user.position, r.user.unit_name].filter(Boolean).join(' · ') || r.user.email}
								</p>
							</div>
							<div class="mt-1.5 min-w-0 flex-1 sm:mt-0">
								<AvailabilityStatus availability={r} />
							</div>
						</div>
					</li>
				{/each}
			</ul>
		{/if}
	{/if}
</div>
