<script lang="ts">
	import {
		byDay,
		endMinutesOnDay,
		layoutDay,
		minutesOf,
		weekDays,
		WEEKDAY_SHORT,
		type CalendarEvent
	} from '$lib/calendar';
	import { addMinutes, formatWallTime, nowLocal, zoneLabel } from '$lib/types/meeting';
	import { eventClasses } from './event-style';

	let {
		anchor,
		today,
		events
	}: {
		/** Any date in the week to show. */
		anchor: string;
		today: string;
		events: CalendarEvent[];
	} = $props();

	const HOUR_PX = 48;

	const days = $derived(weekDays(anchor));
	const perDay = $derived(byDay(events));

	// Office hours by default, stretched to fit anything scheduled outside them.
	const range = $derived.by(() => {
		let first = 7;
		let last = 18;
		for (const day of days) {
			for (const e of perDay.get(day) ?? []) {
				first = Math.min(first, Math.floor(minutesOf(e.start) / 60));
				last = Math.max(last, Math.ceil(endMinutesOnDay(e) / 60));
			}
		}
		return { first, last: Math.min(last, 24) };
	});
	const hours = $derived(Array.from({ length: range.last - range.first }, (_, i) => range.first + i));

	const now = nowLocal();
	const nowTop = $derived((minutesOf(now) - range.first * 60) * (HOUR_PX / 60));
	const showNow = $derived(days.includes(today) && nowTop >= 0 && nowTop <= hours.length * HOUR_PX);

	// Clicking an empty hour starts a one-hour meeting there.
	function slotHref(date: string, hour: number) {
		const start = `${date}T${String(hour).padStart(2, '0')}:00`;
		return `/dashboard/meetings/new?start=${start}&end=${addMinutes(start, 60)}`;
	}

	const top = (min: number) => (min - range.first * 60) * (HOUR_PX / 60);
</script>

<div class="overflow-x-auto rounded-xl border">
	<div class="min-w-[720px]">
		<div class="grid grid-cols-[3.5rem_repeat(7,1fr)] border-b bg-muted/40">
			<div class="px-1 py-2 text-center text-[10px] text-muted-foreground">{zoneLabel()}</div>
			{#each days as date, i (date)}
				<div class="border-s px-2 py-1.5 text-center">
					<div class="text-xs {i >= 5 ? 'text-destructive/70' : 'text-muted-foreground'}">
						{WEEKDAY_SHORT[i]}
					</div>
					<div
						class="mx-auto flex size-7 items-center justify-center rounded-full text-sm tabular-nums {date ===
						today
							? 'bg-primary font-semibold text-primary-foreground'
							: ''}"
					>
						{Number(date.slice(8, 10))}
					</div>
				</div>
			{/each}
		</div>

		<div class="relative grid grid-cols-[3.5rem_repeat(7,1fr)]">
			<!-- Hour labels -->
			<div>
				{#each hours as h (h)}
					<div class="relative border-b text-end" style="height: {HOUR_PX}px">
						<span class="absolute -top-2 right-1.5 text-[10px] text-muted-foreground tabular-nums">
							{h === range.first ? '' : `${String(h).padStart(2, '0')}.00`}
						</span>
					</div>
				{/each}
			</div>

			{#each days as date (date)}
				<div class="relative border-s {date === today ? 'bg-primary/[0.03]' : ''}">
					{#each hours as h (h)}
						<a
							href={slotHref(date, h)}
							class="block border-b hover:bg-muted/50"
							style="height: {HOUR_PX}px"
							aria-label="Rapat baru {date} pukul {h}.00"
						></a>
					{/each}

					{#each layoutDay(perDay.get(date) ?? []) as p (p.event.meeting.id)}
						{@const e = p.event}
						<a
							href="/dashboard/meetings/{e.meeting.id}"
							class="absolute overflow-hidden rounded-md border px-1.5 py-1 text-[11px] leading-tight shadow-xs hover:z-10 hover:opacity-90 {eventClasses(e)}"
							style="top: {top(p.startMin) + 1}px; height: {Math.max(
								top(p.endMin) - top(p.startMin) - 2,
								18
							)}px; left: calc({(p.lane / p.lanes) * 100}% + 2px); width: calc({100 / p.lanes}% - 4px)"
							title="{formatWallTime(e.start)}{e.end ? `–${formatWallTime(e.end)}` : ''} {e.meeting.title}"
						>
							<p class="truncate font-medium">{e.meeting.title}</p>
							<p class="truncate opacity-80 tabular-nums">
								{formatWallTime(e.start)}{e.end ? `–${formatWallTime(e.end)}` : ' · tanpa jam selesai'}
							</p>
						</a>
					{/each}

					{#if showNow && date === today}
						<div class="pointer-events-none absolute inset-x-0 z-20" style="top: {nowTop}px">
							<div class="relative h-px bg-destructive">
								<span class="absolute -top-1 -left-1 size-2 rounded-full bg-destructive"></span>
							</div>
						</div>
					{/if}
				</div>
			{/each}
		</div>
	</div>
</div>
