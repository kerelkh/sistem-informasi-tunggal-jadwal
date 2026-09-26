<script lang="ts">
	import { Badge } from '$lib/components/ui/badge/index.js';
	import { formatRange } from '$lib/types/meeting';
	import type { UserAvailability } from '$lib/types/availability';

	let { availability, compact = false }: { availability: UserAvailability; compact?: boolean } =
		$props();

	const blocking = $derived(availability.busy.filter((b) => b.blocking));
	const soft = $derived(availability.busy.filter((b) => !b.blocking));
</script>

<div class="flex flex-col gap-1">
	<div>
		{#if availability.available}
			<Badge class="bg-emerald-600/10 text-emerald-700 dark:bg-emerald-400/15 dark:text-emerald-300">
				Tersedia
			</Badge>
		{:else}
			<Badge variant="destructive">Sibuk</Badge>
		{/if}
	</div>
	{#if !compact}
		{#each [...blocking, ...soft] as slot (slot.meeting_id)}
			<p class="text-xs {slot.blocking ? 'text-foreground' : 'text-muted-foreground'}">
				<span class="font-medium">{slot.title}</span>
				<span class="text-muted-foreground">
					· {formatRange(slot.scheduled_start, slot.scheduled_end)}
					{#if slot.assumed_end}(tanpa jam selesai — dianggap sepanjang hari){/if}
					{#if slot.tentative}· belum dijawab{:else if !slot.is_formal}· informal{/if}
				</span>
			</p>
		{/each}
	{/if}
</div>
