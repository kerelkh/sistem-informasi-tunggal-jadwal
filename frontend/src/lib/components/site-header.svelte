<script lang="ts">
	import * as Sidebar from '$lib/components/ui/sidebar/index.js';
	import { Separator } from '$lib/components/ui/separator/index.js';
	import NotificationBell from './notification-bell.svelte';
	import ThemeToggle from '$lib/theme-toggle.svelte';

	let { title = 'Beranda' }: { title?: string } = $props();
</script>

<header
	class="flex h-(--header-height) shrink-0 items-center gap-2 border-b transition-[width,height] ease-linear group-has-data-[collapsible=icon]/sidebar-wrapper:h-(--header-height)"
>
	<div class="flex w-full items-center gap-1 px-4 lg:gap-2 lg:px-6">
		<Sidebar.Trigger class="-ms-1" />
		<Separator orientation="vertical" class="mx-2 data-[orientation=vertical]:h-4" />
		<h1 class="font-heading text-base font-medium">{title}</h1>
		<div class="ms-auto flex items-center gap-1">
			<ThemeToggle />
			<NotificationBell />
		</div>
	</div>
</header>
