<script lang="ts">
	import * as Table from '$lib/components/ui/table/index.js';
	import * as AlertDialog from '$lib/components/ui/alert-dialog/index.js';
	import * as Select from '$lib/components/ui/select/index.js';
	import { Badge } from '$lib/components/ui/badge/index.js';
	import { Button } from '$lib/components/ui/button/index.js';
	import { Input } from '$lib/components/ui/input/index.js';
	import { Skeleton } from '$lib/components/ui/skeleton/index.js';
	import SiteHeader from '$lib/components/site-header.svelte';
	import MeetingBadges from '$lib/components/meeting-badges.svelte';
	import RespondDialog from '$lib/components/respond-dialog.svelte';
	import { invalidateAll } from '$app/navigation';
	import {
		effectiveStart,
		formatMeetingDateTime,
		isOnMyCalendar,
		isOrganizer,
		isPendingInvitation,
		isUpcoming as isUpcomingAt,
		locationLabel,
		usesActualDates,
		type MeetingListItem
	} from '$lib/types/meeting';
	import { displayName } from '$lib/types/user';
	import type { PageProps } from './$types';

	let { data }: PageProps = $props();

	let deletingId = $state<number | null>(null);
	let deleting = $state(false);
	let responding = $state<{ meetingId: number; title: string; action: 'decline' | 'cancel' } | null>(
		null
	);

	let query = $state('');
	let categoryFilter = $state('all');
	let roleFilter = $state<'all' | 'organizer' | 'invitee'>('all');
	let view = $state<'all' | 'upcoming' | 'past' | 'unpaid'>('all');

	const VIEWS = [
		{ value: 'all', label: 'Semua rapat' },
		{ value: 'upcoming', label: 'Akan datang' },
		{ value: 'past', label: 'Sudah lewat' },
		{ value: 'unpaid', label: 'Honorarium belum dibayar' }
	] as const;

	const ROLES = [
		{ value: 'all', label: 'Semua peran' },
		{ value: 'organizer', label: 'Saya penyelenggara' },
		{ value: 'invitee', label: 'Saya diundang' }
	] as const;

	const viewLabel = $derived(VIEWS.find((v) => v.value === view)?.label ?? 'Semua rapat');
	const roleLabel = $derived(ROLES.find((r) => r.value === roleFilter)?.label ?? 'Semua peran');

	// Read once per page load rather than per render, so rows can't reshuffle mid-scroll.
	const now = Date.now();

	async function confirmDelete() {
		if (deletingId === null) return;
		deleting = true;
		await fetch(`/api/meetings/${deletingId}`, { method: 'DELETE' });
		deleting = false;
		deletingId = null;
		await invalidateAll();
	}

	function categoriesOf(meetings: MeetingListItem[]) {
		return [...new Set(meetings.flatMap((m) => m.categories))].sort();
	}

	function matches(m: MeetingListItem) {
		if (categoryFilter !== 'all' && !m.categories.includes(categoryFilter)) return false;
		if (roleFilter !== 'all' && m.me.role !== roleFilter) return false;
		const q = query.trim().toLowerCase();
		if (!q) return true;
		return (
			[
				m.title,
				m.inviting_unit,
				m.contact_person,
				m.location_place,
				m.location_city,
				displayName(m.organizer)
			]
				.filter(Boolean)
				.some((f) => f!.toLowerCase().includes(q)) ||
			m.categories.some((c) => c.toLowerCase().includes(q))
		);
	}

	// Once a meeting has run, its actual execution is what places it in time; until
	// then the schedule is all we know. Same rule drives sorting.
	const isUpcoming = (m: MeetingListItem) => isUpcomingAt(m, now);
	const isUnpaid = (m: MeetingListItem) => m.me.has_takehome_pay && !m.me.takehome_pay_paid;

	/**
	 * Upcoming runs soonest-first because the question it answers is "what's next";
	 * past runs newest-first because the question there is "what just happened".
	 */
	function sections(meetings: MeetingListItem[]) {
		const filtered = meetings.filter(matches);
		const byStartAsc = (a: MeetingListItem, b: MeetingListItem) =>
			effectiveStart(a).localeCompare(effectiveStart(b));
		const byStartDesc = (a: MeetingListItem, b: MeetingListItem) =>
			effectiveStart(b).localeCompare(effectiveStart(a));

		if (view === 'unpaid') {
			return [{ label: 'Honorarium belum dibayar', rows: filtered.filter(isUnpaid).sort(byStartDesc) }];
		}
		const upcoming = { label: 'Akan datang', rows: filtered.filter(isUpcoming).sort(byStartAsc) };
		const past = { label: 'Sudah lewat', rows: filtered.filter((m) => !isUpcoming(m)).sort(byStartDesc) };

		if (view === 'upcoming') return [upcoming];
		if (view === 'past') return [past];
		return [upcoming, past];
	}
</script>

<svelte:head>
	<title>Rapat Saya — SITUNG</title>
</svelte:head>

<SiteHeader title="Rapat Saya" />
<div class="flex flex-1 flex-col gap-4 p-4 md:p-6">
	<div class="flex flex-wrap items-center justify-between gap-3">
		<div>
			<h2 class="font-heading text-lg font-semibold">Rapat saya</h2>
			<p class="text-sm text-muted-foreground">
				Rapat yang Anda selenggarakan dan undangan yang sudah Anda terima.
			</p>
		</div>
		<div class="flex items-center gap-2">
			<Button variant="outline" href="/dashboard/calendar">Lihat kalender</Button>
			<Button href="/dashboard/meetings/new">Rapat baru</Button>
		</div>
	</div>

	{#await data.meetings}
		<div class="rounded-xl border">
			<Table.Root>
				<Table.Body>
					{#each { length: 5 } as _, i (i)}
						<Table.Row>
							<Table.Cell><Skeleton class="h-4 w-48" /></Table.Cell>
							<Table.Cell><Skeleton class="h-4 w-32" /></Table.Cell>
							<Table.Cell><Skeleton class="h-4 w-24" /></Table.Cell>
							<Table.Cell><Skeleton class="h-4 w-16" /></Table.Cell>
						</Table.Row>
					{/each}
				</Table.Body>
			</Table.Root>
		</div>
	{:then all}
		{@const meetings = all.filter(isOnMyCalendar)}
		{@const pending = all.filter(isPendingInvitation).length}
		{@const categories = categoriesOf(meetings)}
		{@const groups = sections(meetings)}
		{@const shown = groups.reduce((n, g) => n + g.rows.length, 0)}
		{@const unpaidCount = meetings.filter(isUnpaid).length}

		{#if pending > 0}
			<a
				href="/dashboard/invitations"
				class="flex items-center justify-between gap-3 rounded-xl border border-primary/30 bg-primary/5 p-3 text-sm hover:bg-primary/10"
			>
				<span>
					Ada <strong>{pending}</strong> undangan yang menunggu jawaban Anda.
				</span>
				<span class="font-medium">Lihat &rarr;</span>
			</a>
		{/if}

		<div class="flex flex-wrap items-center gap-2">
			<Input bind:value={query} placeholder="Cari judul, unit, orang, tempat..." class="max-w-xs" />
			<Select.Root type="single" bind:value={view}>
				<Select.Trigger class="w-48">{viewLabel}</Select.Trigger>
				<Select.Content>
					{#each VIEWS as v (v.value)}
						<Select.Item value={v.value}>{v.label}</Select.Item>
					{/each}
				</Select.Content>
			</Select.Root>
			<Select.Root type="single" bind:value={roleFilter}>
				<Select.Trigger class="w-40">{roleLabel}</Select.Trigger>
				<Select.Content>
					{#each ROLES as r (r.value)}
						<Select.Item value={r.value}>{r.label}</Select.Item>
					{/each}
				</Select.Content>
			</Select.Root>
			<Select.Root type="single" bind:value={categoryFilter}>
				<Select.Trigger class="w-44">
					{categoryFilter === 'all' ? 'Semua jenis' : categoryFilter}
				</Select.Trigger>
				<Select.Content>
					<Select.Item value="all">Semua jenis</Select.Item>
					{#each categories as c (c)}
						<Select.Item value={c}>{c}</Select.Item>
					{/each}
				</Select.Content>
			</Select.Root>

			{#if query || categoryFilter !== 'all' || view !== 'all' || roleFilter !== 'all'}
				<Button
					variant="ghost"
					size="sm"
					onclick={() => {
						query = '';
						categoryFilter = 'all';
						roleFilter = 'all';
						view = 'all';
					}}
				>
					Reset
				</Button>
				<span class="text-xs text-muted-foreground">{shown} dari {meetings.length}</span>
			{/if}

			{#if unpaidCount > 0 && view !== 'unpaid'}
				<button
					type="button"
					class="ms-auto text-xs text-muted-foreground underline hover:text-foreground"
					onclick={() => (view = 'unpaid')}
				>
					{unpaidCount} rapat menunggu honorarium
				</button>
			{/if}
		</div>

		{#if meetings.length === 0}
			<div class="rounded-xl border border-dashed py-10 text-center text-muted-foreground">
				Belum ada rapat. Buat rapat baru, atau terima undangan.
			</div>
		{:else if shown === 0}
			<div class="rounded-xl border border-dashed py-10 text-center text-muted-foreground">
				Tidak ada rapat yang cocok dengan filter.
			</div>
		{:else}
			{#each groups as group (group.label)}
				{#if group.rows.length > 0}
					<div class="flex flex-col gap-2">
						<h3 class="text-xs font-medium tracking-wide text-muted-foreground uppercase">
							{group.label}
							<span class="ms-1 font-normal">({group.rows.length})</span>
						</h3>
						<div class="rounded-xl border">
							<Table.Root>
								<Table.Header>
									<Table.Row>
										<Table.Head class="w-[30%] min-w-48">Rapat</Table.Head>
										<Table.Head>Waktu</Table.Head>
										<Table.Head>Lokasi</Table.Head>
										<Table.Head>Unit pengundang</Table.Head>
										<Table.Head>Peserta</Table.Head>
										<Table.Head>Honor</Table.Head>
										<Table.Head class="w-0"></Table.Head>
									</Table.Row>
								</Table.Header>
								<Table.Body>
									{#each group.rows as m (m.id)}
										<Table.Row class={m.status === 'cancelled' ? 'opacity-60' : ''}>
											<Table.Cell class="align-top whitespace-normal">
												<a
													href="/dashboard/meetings/{m.id}"
													class="font-medium hover:underline {m.status === 'cancelled'
														? 'line-through'
														: ''}"
												>
													{m.title}
												</a>
												<div class="mt-1">
													<MeetingBadges meeting={m} />
												</div>
												{#if m.categories.length > 0}
													<div class="mt-1 flex flex-wrap gap-1">
														{#each m.categories as c (c)}
															<Badge variant="outline">{c}</Badge>
														{/each}
													</div>
												{/if}
											</Table.Cell>
											<Table.Cell class="align-top whitespace-nowrap text-muted-foreground">
												{formatMeetingDateTime(effectiveStart(m))}
												{#if usesActualDates(m)}
													<span class="block text-[10px] uppercase">realisasi</span>
												{/if}
											</Table.Cell>
											<Table.Cell class="align-top text-muted-foreground">{locationLabel(m)}</Table.Cell>
											<Table.Cell class="align-top text-muted-foreground">
												{m.inviting_unit ?? '—'}
											</Table.Cell>
											<Table.Cell class="align-top whitespace-nowrap text-muted-foreground">
												{m.accepted_count} hadir
												{#if m.pending_count > 0}
													<span class="block text-xs">{m.pending_count} belum menjawab</span>
												{/if}
											</Table.Cell>
											<Table.Cell class="align-top">
												{#if !m.me.has_takehome_pay}
													<span class="text-muted-foreground">—</span>
												{:else}
													<Badge variant={m.me.takehome_pay_paid ? 'default' : 'outline'}>
														{m.me.takehome_pay_paid ? 'Dibayar' : 'Belum'}
													</Badge>
												{/if}
											</Table.Cell>
											<Table.Cell class="align-top">
												<div class="flex justify-end gap-1 whitespace-nowrap">
													<Button href="/dashboard/meetings/{m.id}" variant="ghost" size="sm">Lihat</Button>
													{#if isOrganizer(m)}
														<Button href="/dashboard/meetings/{m.id}/edit" variant="ghost" size="sm">
															Ubah
														</Button>
														<Button
															variant="ghost"
															size="sm"
															class="text-destructive hover:text-destructive"
															onclick={() => (deletingId = m.id)}
														>
															Hapus
														</Button>
													{:else if m.status === 'scheduled' && isUpcoming(m)}
														<Button
															variant="ghost"
															size="sm"
															class="text-destructive hover:text-destructive"
															onclick={() =>
																(responding = { meetingId: m.id, title: m.title, action: 'cancel' })}
														>
															Batal hadir
														</Button>
													{/if}
												</div>
											</Table.Cell>
										</Table.Row>
									{/each}
								</Table.Body>
							</Table.Root>
						</div>
					</div>
				{/if}
			{/each}
		{/if}
	{:catch}
		<div class="rounded-xl border py-8 text-center text-muted-foreground">
			Rapat tidak dapat dimuat — silakan coba lagi.
		</div>
	{/await}
</div>

<RespondDialog bind:target={responding} />

<AlertDialog.Root open={deletingId !== null} onOpenChange={(open) => !open && (deletingId = null)}>
	<AlertDialog.Content>
		<AlertDialog.Header>
			<AlertDialog.Title>Hapus rapat ini?</AlertDialog.Title>
			<AlertDialog.Description>
				Tindakan ini tidak dapat dibatalkan. Peserta yang masih diundang akan diberi tahu bahwa
				rapat dibatalkan. Untuk tetap menyimpan catatannya, buka rapat lalu pilih Batalkan rapat.
			</AlertDialog.Description>
		</AlertDialog.Header>
		<AlertDialog.Footer>
			<AlertDialog.Cancel>Tidak jadi</AlertDialog.Cancel>
			<AlertDialog.Action disabled={deleting} onclick={confirmDelete}>
				{deleting ? 'Menghapus...' : 'Hapus'}
			</AlertDialog.Action>
		</AlertDialog.Footer>
	</AlertDialog.Content>
</AlertDialog.Root>
