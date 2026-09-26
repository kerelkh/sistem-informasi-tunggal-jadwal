<script lang="ts">
	import * as Sidebar from '$lib/components/ui/sidebar/index.js';
	import { HugeiconsIcon } from '@hugeicons/svelte';
	import { page } from '$app/state';
	import { isNavItemActive, type NavGroup } from '$lib/nav.js';

	let { groups }: { groups: NavGroup[] } = $props();
</script>

{#each groups as group, i (group.label ?? i)}
	<Sidebar.Group>
		{#if group.label}
			<Sidebar.GroupLabel>{group.label}</Sidebar.GroupLabel>
		{/if}
		<Sidebar.GroupContent>
			<Sidebar.Menu>
				{#each group.items as item (item.title)}
					<Sidebar.MenuItem>
						<Sidebar.MenuButton
							tooltipContent={item.title}
							isActive={isNavItemActive(item.url, page.url.pathname)}
						>
							{#snippet child({ props })}
								<a href={item.url} {...props}>
									{#if item.icon}
										<HugeiconsIcon icon={item.icon} strokeWidth={2} />
									{/if}
									<span>{item.title}</span>
								</a>
							{/snippet}
						</Sidebar.MenuButton>
						{#if item.badge}
							<Sidebar.MenuBadge>{item.badge}</Sidebar.MenuBadge>
						{/if}
					</Sidebar.MenuItem>
				{/each}
			</Sidebar.Menu>
		</Sidebar.GroupContent>
	</Sidebar.Group>
{/each}
