<script lang="ts">
	import * as Sidebar from '$lib/components/ui/sidebar/index.js';
	import NavMain from './nav-main.svelte';
	import NavUser from './nav-user.svelte';
	import { page } from '$app/state';
	import { APP_NAME, APP_TAGLINE } from '$lib/config.js';
	import { dashboardNav } from '$lib/nav.js';
	import type { CurrentUser } from '$lib/types/user';
	import type { ComponentProps } from 'svelte';

	const data = $derived(page.data as { user?: CurrentUser; pendingInvitations?: number });
	const groups = $derived(dashboardNav(data.user?.role ?? 'user', data.pendingInvitations ?? 0));

	let { ...restProps }: ComponentProps<typeof Sidebar.Root> = $props();
</script>

<Sidebar.Root collapsible="offcanvas" {...restProps}>
	<Sidebar.Header>
		<Sidebar.Menu>
			<Sidebar.MenuItem>
				<Sidebar.MenuButton size="lg">
					{#snippet child({ props })}
						<a href="/dashboard" {...props}>
							<div
								class="flex aspect-square size-8 items-center justify-center rounded-lg bg-primary font-heading text-sm font-bold text-primary-foreground"
							>
								{APP_NAME.charAt(0)}
							</div>
							<div class="grid flex-1 text-start leading-tight">
								<span class="truncate font-heading font-semibold">{APP_NAME}</span>
								<span class="truncate text-xs text-muted-foreground">{APP_TAGLINE}</span>
							</div>
						</a>
					{/snippet}
				</Sidebar.MenuButton>
			</Sidebar.MenuItem>
		</Sidebar.Menu>
	</Sidebar.Header>
	<Sidebar.Content>
		<NavMain {groups} />
	</Sidebar.Content>
	<Sidebar.Footer>
		{#if data.user}
			<NavUser user={data.user} />
		{/if}
	</Sidebar.Footer>
</Sidebar.Root>
