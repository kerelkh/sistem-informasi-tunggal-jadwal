<script lang="ts">
	import { HugeiconsIcon } from '@hugeicons/svelte';
	import { Add01Icon } from '@hugeicons/core-free-icons';
	import { byDay, monthGrid, WEEKDAY_SHORT, type CalendarEvent } from '$lib/calendar';
	import { formatWallTime } from '$lib/types/meeting';
	import { eventClasses } from './event-style';

	let {
		anchor,
		today,
		events,
		weekHref
	}: {
		/** Any date in the month to show. */
		anchor: string;
		today: string;
		events: CalendarEvent[];
		/** Where "+N more" goes: that day's week, where everything fits. */
		weekHref: (date: string) => string;
	} = $props();

	const MAX_PER_DAY = 3;

	const weeks = $derived(monthGrid(anchor));
	const days = $derived(byDay(events));
	const month = $derived(anchor.slice(0, 7));
</script>

<div class="overflow-hidden rounded-xl border">
	<div class="grid grid-cols-7 border-b bg-muted/40">
		{#each WEEKDAY_SHORT as label, i (label)}
			<div
				class="px-2 py-2 text-center text-xs font-medium {i >= 5
					? 'text-destructive/70'
					: 'text-muted-foreground'}"
			>
				{label}
			</div>
		{/each}
	</div>
	{#each weeks as week (week[0])}
		<div class="grid grid-cols-7 border-b last:border-b-0">
			{#each week as date (date)}
				{@const items = days.get(date) ?? []}
				{@const inMonth = date.slice(0, 7) === month}
				<div
					class="group relative min-h-24 border-e p-1 last:border-e-0 sm:min-h-28 sm:p-1.5 {inMonth
						? ''
						: 'bg-muted/30'}"
				>
					<div class="flex items-center justify-between">
						<span
							class="flex size-6 items-center justify-center rounded-full text-xs tabular-nums {date ===
							today
								? 'bg-primary font-semibold text-primary-foreground'
								: inMonth
									? ''
									: 'text-muted-foreground'}"
						>
							{Number(date.slice(8, 10))}
						</span>
						<a
							href="/dashboard/meetings/new?start={date}T09:00&end={date}T10:00"
							class="hidden rounded-md p-0.5 text-muted-foreground group-hover:block hover:bg-muted hover:text-foreground"
							aria-label="Rapat baru pada tanggal ini"
							title="Rapat baru pada tanggal ini"
						>
							<HugeiconsIcon icon={Add01Icon} strokeWidth={2} class="size-3.5" />
						</a>
					</div>

					<!-- Phones: dots only, the cell is too narrow for titles. -->
					{#if items.length > 0}
						<div class="mt-1 flex flex-wrap gap-0.5 sm:hidden">
							{#each items as e (e.meeting.id)}
								<span class="size-1.5 rounded-full {e.kind === 'organizer' ? 'bg-primary' : e.kind === 'attending' ? 'bg-sky-500' : 'border border-muted-foreground'}"></span>
							{/each}
						</div>
					{/if}

					<ul class="mt-1 hidden flex-col gap-0.5 sm:flex">
						{#each items.slice(0, MAX_PER_DAY) as e (e.meeting.id)}
							<li>
								<a
									href="/dashboard/meetings/{e.meeting.id}"
									class="block truncate rounded-md border px-1.5 py-0.5 text-[11px] leading-tight hover:opacity-80 {eventClasses(e)}"
									title="{formatWallTime(e.start)} {e.meeting.title}"
								>
									<span class="tabular-nums">{formatWallTime(e.start)}</span>
									{e.meeting.title}
								</a>
							</li>
						{/each}
						{#if items.length > MAX_PER_DAY}
							<li>
								<a
									href={weekHref(date)}
									class="block px-1.5 text-[11px] text-muted-foreground hover:text-foreground"
								>
									+{items.length - MAX_PER_DAY} lainnya
								</a>
							</li>
						{/if}
					</ul>
					{#if items.length > 0}
						<a href={weekHref(date)} class="absolute inset-0 sm:hidden" aria-label="Lihat minggu ini"></a>
					{/if}
				</div>
			{/each}
		</div>
	{/each}
</div>
