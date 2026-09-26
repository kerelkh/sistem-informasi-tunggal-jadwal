<script lang="ts">
	import { HugeiconsIcon } from '@hugeicons/svelte';
	import { Moon02Icon, Sun03Icon } from '@hugeicons/core-free-icons';
	import { Button } from '$lib/components/ui/button/index.js';

	let isDark = $state(false);

	$effect(() => {
		const stored = localStorage.getItem('theme');
		const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
		isDark = stored ? stored === 'dark' : prefersDark;
		document.documentElement.classList.toggle('dark', isDark);
	});

	function toggle() {
		isDark = !isDark;
		document.documentElement.classList.toggle('dark', isDark);
		localStorage.setItem('theme', isDark ? 'dark' : 'light');
	}
</script>

<Button variant="ghost" size="icon" onclick={toggle} aria-label="Ganti tema terang/gelap">
	<!-- Two elements, not one with a swapped `icon` prop: HugeiconsIcon draws once and
	     doesn't redraw when the prop changes. -->
	{#if isDark}
		<HugeiconsIcon icon={Sun03Icon} strokeWidth={2} />
	{:else}
		<HugeiconsIcon icon={Moon02Icon} strokeWidth={2} />
	{/if}
</Button>
