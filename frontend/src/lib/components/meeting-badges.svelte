<script lang="ts">
	import { Badge } from '$lib/components/ui/badge/index.js';
	import { PARTICIPANT_STATUS_LABEL, type MeetingListItem } from '$lib/types/meeting';
	import { displayName } from '$lib/types/user';

	let { meeting: m }: { meeting: MeetingListItem } = $props();
</script>

<div class="flex flex-wrap items-center gap-1">
	{#if m.status === 'cancelled'}
		<Badge variant="destructive">Rapat dibatalkan</Badge>
	{/if}
	{#if m.me.role === 'organizer'}
		<Badge>Penyelenggara</Badge>
	{:else}
		<Badge variant="secondary" title="Diundang oleh {displayName(m.organizer)}">
			Diundang · {displayName(m.organizer)}
		</Badge>
		{#if m.me.status !== 'accepted'}
			<Badge variant="outline">{PARTICIPANT_STATUS_LABEL[m.me.status]}</Badge>
		{/if}
	{/if}
	{#if !m.is_formal}
		<Badge variant="outline">informal</Badge>
	{/if}
</div>
