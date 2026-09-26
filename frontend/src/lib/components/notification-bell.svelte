<script lang="ts">
	import { goto, invalidateAll } from '$app/navigation';
	import { page } from '$app/state';
	import { HugeiconsIcon } from '@hugeicons/svelte';
	import {
		CalendarRemove02Icon,
		Cancel01Icon,
		CheckmarkCircle02Icon,
		MailReceive01Icon,
		Notification03Icon,
		PencilEdit02Icon,
		UserRemove01Icon
	} from '@hugeicons/core-free-icons';
	import type { IconSvgElement } from '@hugeicons/svelte';
	import * as DropdownMenu from '$lib/components/ui/dropdown-menu/index.js';
	import { Button } from '$lib/components/ui/button/index.js';
	import { formatMeetingDateTime } from '$lib/types/meeting';
	import type { Notification, NotificationType } from '$lib/types/notification';

	const notifications = $derived((page.data as { notifications?: Notification[] }).notifications ?? []);
	const unreadCount = $derived((page.data as { unreadNotifications?: number }).unreadNotifications ?? 0);

	const ICONS: Record<NotificationType, IconSvgElement> = {
		meeting_invitation: MailReceive01Icon,
		invitation_accepted: CheckmarkCircle02Icon,
		invitation_declined: UserRemove01Icon,
		invitation_cancelled: UserRemove01Icon,
		invitation_revoked: UserRemove01Icon,
		meeting_updated: PencilEdit02Icon,
		meeting_cancelled: CalendarRemove02Icon
	};

	function formatRelative(iso: string) {
		const diffMs = Date.now() - new Date(iso).getTime();
		const minutes = Math.floor(diffMs / 60000);
		if (minutes < 1) return 'baru saja';
		if (minutes < 60) return `${minutes} menit lalu`;
		const hours = Math.floor(minutes / 60);
		if (hours < 24) return `${hours} jam lalu`;
		const days = Math.floor(hours / 24);
		if (days < 7) return `${days} hari lalu`;
		return new Date(iso).toLocaleDateString('id-ID', { day: 'numeric', month: 'short' });
	}

	async function openNotification(notification: Notification) {
		if (!notification.is_read) {
			await fetch(`/api/notifications/${notification.id}/read?is_read=true`, { method: 'PATCH' });
			await invalidateAll();
		}
		if (notification.link) await goto(notification.link);
	}

	async function deleteNotification(e: Event, id: number) {
		e.stopPropagation();
		await fetch(`/api/notifications/${id}`, { method: 'DELETE' });
		await invalidateAll();
	}

	async function markAllRead() {
		await fetch('/api/notifications/mark-all-read', { method: 'POST' });
		await invalidateAll();
	}
</script>

<DropdownMenu.Root>
	<DropdownMenu.Trigger>
		{#snippet child({ props })}
			<Button {...props} variant="ghost" size="icon" class="relative" aria-label="Notifikasi">
				<HugeiconsIcon icon={Notification03Icon} strokeWidth={2} />
				{#if unreadCount > 0}
					<span
						class="absolute top-1 right-1 flex size-4 items-center justify-center rounded-full bg-destructive text-[10px] font-medium text-white"
					>
						{unreadCount > 9 ? '9+' : unreadCount}
					</span>
				{/if}
			</Button>
		{/snippet}
	</DropdownMenu.Trigger>
	<DropdownMenu.Content align="end" class="w-80">
		<div class="flex items-center justify-between px-2 py-1.5">
			<DropdownMenu.Label class="p-0">Notifikasi</DropdownMenu.Label>
			{#if unreadCount > 0}
				<button
					type="button"
					class="text-xs text-muted-foreground hover:text-foreground"
					onclick={markAllRead}
				>
					Tandai semua dibaca
				</button>
			{/if}
		</div>
		<DropdownMenu.Separator />
		{#if notifications.length === 0}
			<p class="px-2 py-6 text-center text-xs text-muted-foreground">Tidak ada notifikasi.</p>
		{:else}
			<div class="flex max-h-96 flex-col overflow-y-auto">
				{#each notifications as notification (notification.id)}
					<div
						role="button"
						tabindex="0"
						class="group flex w-full items-start gap-2 rounded-lg px-2 py-2 text-left hover:bg-accent {notification.is_read
							? ''
							: 'bg-muted/60'}"
						onclick={() => openNotification(notification)}
						onkeydown={(e) => e.key === 'Enter' && openNotification(notification)}
					>
						<HugeiconsIcon
							icon={ICONS[notification.type]}
							strokeWidth={2}
							class="mt-0.5 size-4 shrink-0 text-muted-foreground"
						/>
						<div class="min-w-0 flex-1">
							<p class="line-clamp-2 text-xs font-medium">{notification.title}</p>
							{#if notification.body || notification.event_at}
								<!-- event_at is an instant, so each reader sees it on their own clock. -->
								<p class="truncate text-xs text-muted-foreground">
									{[notification.body, notification.event_at && formatMeetingDateTime(notification.event_at)]
										.filter(Boolean)
										.join(' · ')}
								</p>
							{/if}
							<p class="mt-0.5 text-[10px] text-muted-foreground">
								{formatRelative(notification.created_at)}
							</p>
						</div>
						<button
							type="button"
							aria-label="Hapus notifikasi"
							class="shrink-0 rounded-md p-1 text-muted-foreground opacity-0 group-hover:opacity-100 hover:text-foreground focus:opacity-100"
							onclick={(e) => deleteNotification(e, notification.id)}
						>
							<HugeiconsIcon icon={Cancel01Icon} strokeWidth={2} class="size-3" />
						</button>
					</div>
				{/each}
			</div>
		{/if}
	</DropdownMenu.Content>
</DropdownMenu.Root>
