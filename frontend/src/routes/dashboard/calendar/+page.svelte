<script lang="ts">
	import { page } from '$app/state';
	import { HugeiconsIcon } from '@hugeicons/svelte';
	import { ArrowLeft01Icon, ArrowRight01Icon } from '@hugeicons/core-free-icons';
	import { Button } from '$lib/components/ui/button/index.js';
	import { Label } from '$lib/components/ui/label/index.js';
	import { Skeleton } from '$lib/components/ui/skeleton/index.js';
	import { Switch } from '$lib/components/ui/switch/index.js';
	import * as Tabs from '$lib/components/ui/tabs/index.js';
	import SiteHeader from '$lib/components/site-header.svelte';
	import MonthView from '$lib/components/calendar/month-view.svelte';
	import WeekView from '$lib/components/calendar/week-view.svelte';
	import CalendarLegend from '$lib/components/calendar/calendar-legend.svelte';
	import { goto } from '$app/navigation';
	import {
		monthTitle,
		shiftMonth,
		toEvents,
		todayLocal,
		weekTitle,
		type CalendarView
	} from '$lib/calendar';
	import { addDays } from '$lib/types/meeting';
	import type { PageProps } from './$types';

	let { data }: PageProps = $props();

	const today = todayLocal();

	// View and date live in the URL, so a view can be bookmarked or shared and the
	// back button steps through the months you looked at.
	const view = $derived<CalendarView>(page.url.searchParams.get('view') === 'week' ? 'week' : 'month');
	const anchor = $derived.by(() => {
		const d = page.url.searchParams.get('date');
		return d && /^\d{4}-\d{2}-\d{2}$/.test(d) ? d : today;
	});

	let includePending = $state(true);

	function href(v: CalendarView, date: string) {
		return `/dashboard/calendar?view=${v}&date=${date}`;
	}

	const prev = $derived(view === 'month' ? shiftMonth(anchor, -1) : addDays(anchor, -7));
	const next = $derived(view === 'month' ? shiftMonth(anchor, 1) : addDays(anchor, 7));
	const title = $derived(view === 'month' ? monthTitle(anchor) : weekTitle(anchor));
</script>

<svelte:head>
	<title>Kalender — SITUNG</title>
</svelte:head>

<SiteHeader title="Kalender" />
<div class="flex flex-1 flex-col gap-4 p-4 md:p-6">
	<div class="flex flex-wrap items-center justify-between gap-3">
		<div class="flex items-center gap-2">
			<Button variant="outline" size="sm" href={href(view, today)}>Hari ini</Button>
			<div class="flex items-center">
				<Button variant="ghost" size="icon-sm" href={href(view, prev)} aria-label="Sebelumnya">
					<HugeiconsIcon icon={ArrowLeft01Icon} strokeWidth={2} />
				</Button>
				<Button variant="ghost" size="icon-sm" href={href(view, next)} aria-label="Berikutnya">
					<HugeiconsIcon icon={ArrowRight01Icon} strokeWidth={2} />
				</Button>
			</div>
			<h2 class="font-heading text-lg font-semibold">{title}</h2>
		</div>
		<div class="flex flex-wrap items-center gap-3">
			<Tabs.Root value={view} onValueChange={(v) => goto(href(v as CalendarView, anchor))}>
				<Tabs.List>
					<Tabs.Trigger value="month">Bulan</Tabs.Trigger>
					<Tabs.Trigger value="week">Minggu</Tabs.Trigger>
				</Tabs.List>
			</Tabs.Root>
			<Button href="/dashboard/meetings/new">Rapat baru</Button>
		</div>
	</div>

	<div class="flex flex-wrap items-center justify-between gap-3">
		<CalendarLegend />
		<div class="flex items-center gap-2">
			<Switch id="include-pending" bind:checked={includePending} />
			<Label for="include-pending" class="text-xs font-normal">Tampilkan undangan belum dijawab</Label>
		</div>
	</div>

	{#await data.meetings}
		<Skeleton class="h-[32rem] w-full rounded-xl" />
	{:then meetings}
		{@const events = toEvents(meetings, includePending)}
		{#if view === 'month'}
			<MonthView {anchor} {today} {events} weekHref={(date) => href('week', date)} />
		{:else}
			<WeekView {anchor} {today} {events} />
		{/if}
	{:catch}
		<div class="rounded-xl border py-8 text-center text-muted-foreground">
			Kalender tidak dapat dimuat — silakan coba lagi.
		</div>
	{/await}
</div>
