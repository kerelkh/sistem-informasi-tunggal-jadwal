<script lang="ts">
	import * as Card from '$lib/components/ui/card/index.js';
	import { Button } from '$lib/components/ui/button/index.js';
	import { Skeleton } from '$lib/components/ui/skeleton/index.js';
	import SiteHeader from '$lib/components/site-header.svelte';
	import MeetingBadges from '$lib/components/meeting-badges.svelte';
	import {
		addDays,
		formatLongDate,
		formatRange,
		formatTime,
		isOnMyCalendar,
		isPendingInvitation,
		locationLabel,
		nowLocal,
		toLocalWall,
		type MeetingListItem
	} from '$lib/types/meeting';
	import { displayName } from '$lib/types/user';
	import type { PageProps } from './$types';

	let { data }: PageProps = $props();

	// "Today" is today on the viewer's own clock. Meetings are converted to that clock
	// before comparing, so local wall-clock strings compare correctly as text.
	const nowInput = nowLocal();
	const today = nowInput.slice(0, 10);
	const weekAhead = addDays(nowInput, 7);

	const greeting = (() => {
		const h = Number(nowInput.slice(11, 13));
		return h < 11 ? 'Selamat pagi' : h < 15 ? 'Selamat siang' : h < 18 ? 'Selamat sore' : 'Selamat malam';
	})();

	function summarize(all: MeetingListItem[]) {
		const live = all.filter((m) => isOnMyCalendar(m) && m.status === 'scheduled');
		const localStart = (m: MeetingListItem) => toLocalWall(m.scheduled_start);
		const byStart = (a: MeetingListItem, b: MeetingListItem) =>
			a.scheduled_start.localeCompare(b.scheduled_start);
		return {
			today: live.filter((m) => localStart(m).slice(0, 10) === today).sort(byStart),
			upcoming: live
				.filter((m) => localStart(m).slice(0, 10) > today && localStart(m) <= weekAhead)
				.sort(byStart),
			pending: all.filter(isPendingInvitation),
			unpaid: all.filter((m) => m.me.has_takehome_pay && !m.me.takehome_pay_paid).length
		};
	}
</script>

<svelte:head>
	<title>Beranda — SITUNG</title>
</svelte:head>

<SiteHeader title="Beranda" />
<div class="flex flex-1 flex-col gap-6 p-4 md:p-6">
	<div class="flex flex-wrap items-end justify-between gap-3">
		<div>
			<h2 class="font-heading text-2xl font-semibold tracking-tight">
				{greeting}, {displayName(data.user)}
			</h2>
			<p class="text-sm text-muted-foreground">
				{formatLongDate(today)}{data.user.unit ? ` · ${data.user.unit.name}` : ''}
			</p>
		</div>
		<div class="flex gap-2">
			<Button variant="outline" href="/dashboard/availability">Siapa yang tersedia?</Button>
			<Button href="/dashboard/meetings/new">Rapat baru</Button>
		</div>
	</div>

	{#await data.meetings}
		<div class="grid gap-4 md:grid-cols-3">
			{#each { length: 3 } as _, i (i)}
				<Skeleton class="h-28 rounded-xl" />
			{/each}
		</div>
	{:then all}
		{@const s = summarize(all)}
		<div class="grid gap-4 sm:grid-cols-3">
			<Card.Root>
				<Card.Header>
					<Card.Description>Hari ini</Card.Description>
					<Card.Title class="text-3xl tabular-nums">{s.today.length}</Card.Title>
				</Card.Header>
				<Card.Content class="text-xs text-muted-foreground">
					rapat di kalender Anda
				</Card.Content>
			</Card.Root>
			<a href="/dashboard/invitations" class="group">
				<Card.Root class="h-full group-hover:bg-muted/40">
					<Card.Header>
						<Card.Description>Undangan</Card.Description>
						<Card.Title class="text-3xl tabular-nums">{s.pending.length}</Card.Title>
					</Card.Header>
					<Card.Content class="text-xs text-muted-foreground">menunggu jawaban Anda</Card.Content>
				</Card.Root>
			</a>
			<Card.Root>
				<Card.Header>
					<Card.Description>Honorarium</Card.Description>
					<Card.Title class="text-3xl tabular-nums">{s.unpaid}</Card.Title>
				</Card.Header>
				<Card.Content class="text-xs text-muted-foreground">
					rapat belum dibayar
				</Card.Content>
			</Card.Root>
		</div>

		<div class="grid gap-6 lg:grid-cols-2">
			<Card.Root>
				<Card.Header>
					<Card.Title>Jadwal hari ini</Card.Title>
				</Card.Header>
				<Card.Content>
					{#if s.today.length === 0}
						<p class="py-6 text-center text-sm text-muted-foreground">Tidak ada rapat hari ini.</p>
					{:else}
						<ol class="flex flex-col gap-3">
							{#each s.today as m (m.id)}
								<li class="flex gap-3">
									<div
										class="w-14 shrink-0 pt-0.5 text-sm font-medium tabular-nums {toLocalWall(m.scheduled_start) <
										nowInput
											? 'text-muted-foreground'
											: ''}"
									>
										{formatTime(m.scheduled_start)}
									</div>
									<div class="min-w-0 flex-1 border-s ps-3">
										<a href="/dashboard/meetings/{m.id}" class="text-sm font-medium hover:underline">
											{m.title}
										</a>
										<p class="text-xs text-muted-foreground">
											{m.scheduled_end ? `sampai ${formatTime(m.scheduled_end)} · ` : ''}{locationLabel(m)}
										</p>
										<div class="mt-1"><MeetingBadges meeting={m} /></div>
									</div>
								</li>
							{/each}
						</ol>
					{/if}
				</Card.Content>
			</Card.Root>

			<Card.Root>
				<Card.Header>
					<Card.Title>7 hari ke depan</Card.Title>
					<Card.Action>
						<Button variant="ghost" size="sm" href="/dashboard/calendar">Buka kalender</Button>
					</Card.Action>
				</Card.Header>
				<Card.Content>
					{#if s.upcoming.length === 0}
						<p class="py-6 text-center text-sm text-muted-foreground">Tidak ada rapat dalam seminggu ke depan.</p>
					{:else}
						<ul class="flex flex-col divide-y">
							{#each s.upcoming as m (m.id)}
								<li class="py-2.5 first:pt-0 last:pb-0">
									<a href="/dashboard/meetings/{m.id}" class="text-sm font-medium hover:underline">
										{m.title}
									</a>
									<p class="text-xs text-muted-foreground">
										{formatRange(m.scheduled_start, m.scheduled_end)} · {locationLabel(m)}
									</p>
								</li>
							{/each}
						</ul>
					{/if}
				</Card.Content>
			</Card.Root>
		</div>
	{/await}
</div>
