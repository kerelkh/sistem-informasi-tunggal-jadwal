<script lang="ts" module>
	export interface SlashCommandItem {
		title: string;
		icon: import('@hugeicons/svelte').IconSvgElement;
		command: (props: { editor: import('@tiptap/core').Editor; range: import('@tiptap/core').Range }) => void;
	}
</script>

<script lang="ts">
	import { HugeiconsIcon } from '@hugeicons/svelte';
	let {
		items,
		selectedIndex,
		command
	}: {
		items: SlashCommandItem[];
		selectedIndex: number;
		command: (item: SlashCommandItem) => void;
	} = $props();
</script>

<div
	class="z-50 flex w-64 flex-col gap-0.5 rounded-xl border border-border bg-popover p-1 text-popover-foreground shadow-md"
>
	{#if items.length === 0}
		<p class="px-2 py-1.5 text-xs text-muted-foreground">Tidak ditemukan</p>
	{:else}
		{#each items as item, i (item.title)}
			<button
				type="button"
				class="flex items-center gap-2 rounded-lg px-2 py-1.5 text-left text-xs {i === selectedIndex
					? 'bg-accent text-accent-foreground'
					: 'hover:bg-muted'}"
				onclick={() => command(item)}
			>
				<HugeiconsIcon icon={item.icon} strokeWidth={2} class="size-4 shrink-0" />
				{item.title}
			</button>
		{/each}
	{/if}
</div>
