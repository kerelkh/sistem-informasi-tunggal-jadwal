<script lang="ts">
	import { page } from '$app/state';
	import { HugeiconsIcon } from '@hugeicons/svelte';
	import { Search01Icon } from '@hugeicons/core-free-icons';
	import * as Avatar from '$lib/components/ui/avatar/index.js';
	import * as Select from '$lib/components/ui/select/index.js';
	import { Button } from '$lib/components/ui/button/index.js';
	import { Input } from '$lib/components/ui/input/index.js';
	import { Skeleton } from '$lib/components/ui/skeleton/index.js';
	import AvailabilityStatus from './availability-status.svelte';
	import { fetchAvailability, type UserAvailability } from '$lib/types/availability';
	import { displayName, initials, type CurrentUser, type Unit, type UserBrief } from '$lib/types/user';

	let {
		start,
		end = '',
		units,
		excludeMeetingId,
		pickedIds = [],
		pickLabel = 'Undang',
		onpick
	}: {
		/** The slot being checked, as "YYYY-MM-DDTHH:mm". Nothing can be checked without a start. */
		start: string;
		end?: string;
		units: Unit[];
		/** When editing a meeting, its own attendees shouldn't clash with it. */
		excludeMeetingId?: number;
		/** Already invited or staged — shown as done instead of offering the action again. */
		pickedIds?: number[];
		pickLabel?: string;
		onpick: (user: UserBrief) => void | Promise<void>;
	} = $props();

	const me = $derived((page.data as { user?: CurrentUser }).user);

	let query = $state('');
	// Start on the viewer's own unit: most invitations stay close to home.
	let unitFilter = $state(String((page.data as { user?: CurrentUser }).user?.unit?.id ?? 'all'));
	let results = $state<UserAvailability[]>([]);
	// Starts true so the server-rendered page shows a skeleton, not "nobody matches",
	// until the first check comes back.
	let loading = $state(true);
	let error = $state('');
	let pickingId = $state<number | null>(null);

	const unitLabel = $derived(
		unitFilter === 'all' ? 'Semua unit kerja' : (units.find((u) => String(u.id) === unitFilter)?.name ?? 'Unit kerja')
	);

	// Re-query whenever the slot or the filters change, debounced so typing a name
	// doesn't fire a request per keystroke. Stale responses are dropped.
	let requestSeq = 0;
	$effect(() => {
		const args = { start, end, q: query, unitFilter };
		if (!args.start) {
			results = [];
			return;
		}
		const seq = ++requestSeq;
		loading = true;
		const timer = setTimeout(async () => {
			try {
				const data = await fetchAvailability({
					start: args.start,
					end: args.end || undefined,
					q: args.q,
					unitId: args.unitFilter === 'all' ? null : Number(args.unitFilter),
					excludeMeetingId
				});
				if (seq !== requestSeq) return;
				results = data.users.filter((u) => u.user.id !== me?.id);
				error = '';
			} catch (e) {
				if (seq !== requestSeq) return;
				error = e instanceof Error ? e.message : 'Ketersediaan tidak dapat diperiksa.';
			} finally {
				if (seq === requestSeq) loading = false;
			}
		}, 250);
		return () => clearTimeout(timer);
	});

	async function pick(user: UserBrief) {
		pickingId = user.id;
		try {
			await onpick(user);
		} finally {
			pickingId = null;
		}
	}
</script>

<div class="flex flex-col gap-3">
	<div class="flex flex-wrap gap-2">
		<div class="relative min-w-48 flex-1">
			<HugeiconsIcon
				icon={Search01Icon}
				strokeWidth={2}
				class="pointer-events-none absolute top-1/2 left-3 size-4 -translate-y-1/2 text-muted-foreground"
			/>
			<Input bind:value={query} placeholder="Cari nama, email, jabatan..." class="ps-9" />
		</div>
		<Select.Root type="single" bind:value={unitFilter}>
			<Select.Trigger class="w-48">{unitLabel}</Select.Trigger>
			<Select.Content>
				<Select.Item value="all">Semua unit kerja</Select.Item>
				{#each units as u (u.id)}
					<Select.Item value={String(u.id)}>{u.name}</Select.Item>
				{/each}
			</Select.Content>
		</Select.Root>
	</div>

	{#if !start}
		<p class="rounded-xl border border-dashed p-4 text-center text-sm text-muted-foreground">
			Isi waktu mulai rapat terlebih dahulu — lalu Anda dapat melihat siapa yang tersedia.
		</p>
	{:else if error}
		<p class="text-sm text-destructive">{error}</p>
	{:else if loading && results.length === 0}
		<div class="flex flex-col gap-2">
			{#each { length: 3 } as _, i (i)}
				<Skeleton class="h-14 w-full rounded-xl" />
			{/each}
		</div>
	{:else if results.length === 0}
		<p class="rounded-xl border border-dashed p-4 text-center text-sm text-muted-foreground">
			Tidak ada yang cocok dengan pencarian.
		</p>
	{:else}
		<ul class="flex max-h-96 flex-col divide-y overflow-y-auto rounded-xl border {loading ? 'opacity-60' : ''}">
			{#each results as r (r.user.id)}
				{@const picked = pickedIds.includes(r.user.id)}
				<li class="flex items-start gap-3 p-3">
					<Avatar.Root class="size-8">
						<Avatar.Fallback class="text-xs">{initials(r.user)}</Avatar.Fallback>
					</Avatar.Root>
					<div class="min-w-0 flex-1">
						<p class="truncate text-sm font-medium">{displayName(r.user)}</p>
						<p class="truncate text-xs text-muted-foreground">
							{[r.user.position, r.user.unit_name].filter(Boolean).join(' · ') || r.user.email}
						</p>
						<div class="mt-1.5">
							<AvailabilityStatus availability={r} />
						</div>
					</div>
					<Button
						size="sm"
						variant={picked ? 'secondary' : 'default'}
						disabled={picked || !r.available || pickingId !== null}
						onclick={() => pick(r.user)}
					>
						{#if picked}
							Ditambahkan
						{:else if !r.available}
							Sibuk
						{:else}
							{pickingId === r.user.id ? '...' : pickLabel}
						{/if}
					</Button>
				</li>
			{/each}
		</ul>
	{/if}
</div>
