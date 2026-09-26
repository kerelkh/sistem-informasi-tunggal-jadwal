<script lang="ts">
	import { invalidateAll } from '$app/navigation';
	import * as Card from '$lib/components/ui/card/index.js';
	import { Badge } from '$lib/components/ui/badge/index.js';
	import { Button } from '$lib/components/ui/button/index.js';
	import SiteHeader from '$lib/components/site-header.svelte';
	import RespondDialog from '$lib/components/respond-dialog.svelte';
	import AvailabilityStatus from '$lib/components/availability-status.svelte';
	import {
		PARTICIPANT_STATUS_LABEL,
		formatRange,
		isPendingInvitation,
		locationLabel,
		toDateTimeInput,
		type MeetingListItem
	} from '$lib/types/meeting';
	import { fetchAvailability, type UserAvailability } from '$lib/types/availability';
	import { displayName } from '$lib/types/user';
	import { errorMessage } from '$lib/utils/http';
	import type { PageProps } from './$types';

	let { data }: PageProps = $props();

	const pending = $derived(
		data.meetings
			.filter(isPendingInvitation)
			.sort((a, b) => a.scheduled_start.localeCompare(b.scheduled_start))
	);
	const answered = $derived(
		data.meetings
			.filter((m) => !isPendingInvitation(m))
			.sort((a, b) => b.scheduled_start.localeCompare(a.scheduled_start))
			.slice(0, 20)
	);

	let responding = $state<{ meetingId: number; title: string; action: 'decline' | 'cancel' } | null>(
		null
	);
	let acceptingId = $state<number | null>(null);
	let error = $state('');

	// For each pending invitation: would accepting clash with something already on my
	// calendar? The invitation itself is left out of the check.
	let clashes = $state<Record<number, UserAvailability>>({});
	$effect(() => {
		const me = data.user;
		for (const m of pending) {
			fetchAvailability({
				start: toDateTimeInput(m.scheduled_start),
				end: toDateTimeInput(m.scheduled_end) || undefined,
				userIds: [me.id],
				excludeMeetingId: m.id
			})
				.then((res) => {
					if (res.users[0]) clashes[m.id] = res.users[0];
				})
				.catch(() => {});
		}
	});

	async function accept(m: MeetingListItem) {
		acceptingId = m.id;
		error = '';
		const res = await fetch(`/api/meetings/${m.id}/respond`, {
			method: 'POST',
			headers: { 'Content-Type': 'application/json' },
			body: JSON.stringify({ action: 'accept' })
		});
		acceptingId = null;
		if (!res.ok) {
			error = await errorMessage(res);
			return;
		}
		await invalidateAll();
	}
</script>

<svelte:head>
	<title>Undangan — SITUNG</title>
</svelte:head>

<SiteHeader title="Undangan" />
<div class="flex flex-1 flex-col gap-6 p-4 md:p-6">
	<div>
		<h2 class="font-heading text-lg font-semibold">Menunggu jawaban Anda</h2>
		<p class="text-sm text-muted-foreground">
			Jika diterima, rapat masuk ke kalender Anda. Jika ditolak, penyelenggara diberi tahu bahwa Anda tidak dapat hadir.
		</p>
	</div>

	{#if error}
		<p class="rounded-xl border border-destructive/40 bg-destructive/5 p-3 text-sm text-destructive">
			{error}
		</p>
	{/if}

	{#if pending.length === 0}
		<div class="rounded-xl border border-dashed py-10 text-center text-muted-foreground">
			Tidak ada undangan yang menunggu jawaban.
		</div>
	{:else}
		<div class="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
			{#each pending as m (m.id)}
				{@const clash = clashes[m.id]}
				<Card.Root>
					<Card.Header>
						<Card.Description>Dari {displayName(m.organizer)}</Card.Description>
						<Card.Title class="leading-snug">
							<a href="/dashboard/meetings/{m.id}" class="hover:underline">{m.title}</a>
						</Card.Title>
					</Card.Header>
					<Card.Content class="flex flex-col gap-2 text-sm">
						<p>{formatRange(m.scheduled_start, m.scheduled_end)}</p>
						<p class="text-muted-foreground">{locationLabel(m)}</p>
						{#if m.inviting_unit}
							<p class="text-muted-foreground">Undangan dari {m.inviting_unit}</p>
						{/if}
						{#if clash && clash.busy.length > 0}
							<div class="mt-1 rounded-lg bg-muted/60 p-2">
								<p class="mb-1 text-xs font-medium">Jadwal Anda pada waktu tersebut:</p>
								<AvailabilityStatus availability={clash} />
							</div>
						{/if}
					</Card.Content>
					<Card.Footer class="gap-2">
						<Button
							variant="outline"
							class="flex-1"
							onclick={() => (responding = { meetingId: m.id, title: m.title, action: 'decline' })}
						>
							Tolak
						</Button>
						<Button class="flex-1" disabled={acceptingId === m.id} onclick={() => accept(m)}>
							{acceptingId === m.id ? 'Memproses...' : 'Terima'}
						</Button>
					</Card.Footer>
				</Card.Root>
			{/each}
		</div>
	{/if}

	{#if answered.length > 0}
		<div class="flex flex-col gap-2">
			<h3 class="text-xs font-medium tracking-wide text-muted-foreground uppercase">
				Baru dijawab
			</h3>
			<ul class="flex flex-col divide-y rounded-xl border">
				{#each answered as m (m.id)}
					<li class="flex flex-wrap items-center justify-between gap-2 p-3 text-sm">
						<div class="min-w-0">
							<a href="/dashboard/meetings/{m.id}" class="font-medium hover:underline">{m.title}</a>
							<p class="text-xs text-muted-foreground">
								{formatRange(m.scheduled_start, m.scheduled_end)} · dari {displayName(m.organizer)}
							</p>
						</div>
						{#if m.status === 'cancelled'}
							<Badge variant="destructive">Rapat dibatalkan</Badge>
						{:else}
							<Badge variant={m.me.status === 'accepted' ? 'default' : 'outline'}>
								{PARTICIPANT_STATUS_LABEL[m.me.status]}
							</Badge>
						{/if}
					</li>
				{/each}
			</ul>
		</div>
	{/if}
</div>

<RespondDialog bind:target={responding} />
