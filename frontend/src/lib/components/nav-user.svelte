<script lang="ts">
	import { HugeiconsIcon } from '@hugeicons/svelte';
	import { Logout03Icon, MoreVerticalIcon, Settings02Icon } from '@hugeicons/core-free-icons';
	import { goto, invalidateAll } from '$app/navigation';
	import * as Avatar from '$lib/components/ui/avatar/index.js';
	import * as DropdownMenu from '$lib/components/ui/dropdown-menu/index.js';
	import * as Sidebar from '$lib/components/ui/sidebar/index.js';
	import { displayName, initials, type CurrentUser } from '$lib/types/user';

	let { user }: { user: CurrentUser } = $props();

	const sidebar = Sidebar.useSidebar();
	const subtitle = $derived(user.unit?.name ?? (user.role === 'admin' ? 'Administrator' : user.email));

	async function logout() {
		await fetch('/logout', { method: 'POST' });
		await invalidateAll();
		await goto('/login');
	}
</script>

<Sidebar.Menu>
	<Sidebar.MenuItem>
		<DropdownMenu.Root>
			<DropdownMenu.Trigger>
				{#snippet child({ props })}
					<Sidebar.MenuButton
						{...props}
						size="lg"
						class="data-[state=open]:bg-sidebar-accent data-[state=open]:text-sidebar-accent-foreground"
					>
						<Avatar.Root class="size-8 rounded-lg">
							<Avatar.Fallback class="rounded-lg">{initials(user)}</Avatar.Fallback>
						</Avatar.Root>
						<div class="grid flex-1 text-start text-sm leading-tight">
							<span class="truncate font-medium">{displayName(user)}</span>
							<span class="truncate text-xs text-muted-foreground">{subtitle}</span>
						</div>
						<HugeiconsIcon icon={MoreVerticalIcon} strokeWidth={2} class="ms-auto size-4" />
					</Sidebar.MenuButton>
				{/snippet}
			</DropdownMenu.Trigger>
			<DropdownMenu.Content
				class="w-(--bits-dropdown-menu-anchor-width) min-w-56"
				side={sidebar.isMobile ? 'bottom' : 'right'}
				align="end"
				sideOffset={4}
			>
				<DropdownMenu.Label class="p-0 font-normal">
					<div class="flex items-center gap-2 px-1 py-1.5 text-start text-sm">
						<Avatar.Root class="size-8 rounded-lg">
							<Avatar.Fallback class="rounded-lg">{initials(user)}</Avatar.Fallback>
						</Avatar.Root>
						<div class="grid flex-1 text-start text-sm leading-tight">
							<span class="truncate font-medium">{displayName(user)}</span>
							<span class="truncate text-xs text-muted-foreground">{user.email}</span>
						</div>
					</div>
				</DropdownMenu.Label>
				<DropdownMenu.Separator />
				<DropdownMenu.Group>
					<DropdownMenu.Item>
						{#snippet child({ props })}
							<a href="/dashboard/settings" {...props}>
								<HugeiconsIcon icon={Settings02Icon} strokeWidth={2} />
								Pengaturan akun
							</a>
						{/snippet}
					</DropdownMenu.Item>
				</DropdownMenu.Group>
				<DropdownMenu.Separator />
				<DropdownMenu.Item onSelect={logout}>
					<HugeiconsIcon icon={Logout03Icon} strokeWidth={2} />
					Keluar
				</DropdownMenu.Item>
			</DropdownMenu.Content>
		</DropdownMenu.Root>
	</Sidebar.MenuItem>
</Sidebar.Menu>
