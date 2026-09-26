<script lang="ts">
	import type { Snippet } from 'svelte';
	import ThemeToggle from '$lib/theme-toggle.svelte';
	import { APP_NAME, APP_TAGLINE } from '$lib/config.js';

	let { children }: { children: Snippet } = $props();
</script>

<div class="relative flex min-h-svh w-full flex-col items-center justify-center bg-muted/40 px-4 py-16">
	<div class="absolute top-4 right-4">
		<ThemeToggle />
	</div>

	<div class="mb-8 flex flex-col items-center gap-2 text-center">
		<div
			class="flex size-11 items-center justify-center rounded-xl bg-primary font-heading text-lg font-bold text-primary-foreground"
		>
			{APP_NAME.charAt(0)}
		</div>
		<div>
			<p class="font-heading text-xl font-semibold tracking-tight">{APP_NAME}</p>
			<p class="text-sm text-muted-foreground">{APP_TAGLINE}</p>
		</div>
	</div>

	{@render children()}
</div>
