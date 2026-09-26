<script lang="ts">
	import { goto, invalidateAll } from '$app/navigation';
	import * as AlertDialog from '$lib/components/ui/alert-dialog/index.js';
	import * as Avatar from '$lib/components/ui/avatar/index.js';
	import * as Card from '$lib/components/ui/card/index.js';
	import * as Dialog from '$lib/components/ui/dialog/index.js';
	import { Badge } from '$lib/components/ui/badge/index.js';
	import { Button } from '$lib/components/ui/button/index.js';
	import { Checkbox } from '$lib/components/ui/checkbox/index.js';
	import { Label } from '$lib/components/ui/label/index.js';
	import { Separator } from '$lib/components/ui/separator/index.js';
	import SiteHeader from '$lib/components/site-header.svelte';
	import MeetingBadges from '$lib/components/meeting-badges.svelte';
	import PeoplePicker from '$lib/components/people-picker.svelte';
	import RespondDialog from '$lib/components/respond-dialog.svelte';
	import NoteContentView from '$lib/components/editor/note-content-view.svelte';
	import {
		LOCATION_TYPE_LABEL,
		PARTICIPANT_STATUS_LABEL,
		formatMeetingDateTime,
		formatRange,
		formatTimeIn,
		locationLabel,
		toDateTimeInput,
		viewerTimezone,
		type Participant
	} from '$lib/types/meeting';
	import { displayName, initials, type UserBrief } from '$lib/types/user';
	import { errorMessage } from '$lib/utils/http';
	import type { PageProps } from './$types';

	let { data }: PageProps = $props();

	const m = $derived(data.meeting);
	const hasRun = $derived(!!m.actual_start);
	const isOrganizer = $derived(m.me.role === 'organizer');
	const isScheduled = $derived(m.status === 'scheduled');

	const details = $derived([
		{ label: 'Jadwal mulai', value: formatMeetingDateTime(m.scheduled_start) },
		{ label: 'Jadwal selesai', value: formatMeetingDateTime(m.scheduled_end) },
		{ label: 'Realisasi mulai', value: formatMeetingDateTime(m.actual_start) },
		{ label: 'Realisasi selesai', value: formatMeetingDateTime(m.actual_end) },
		{ label: 'Lokasi', value: locationLabel(m) },
		{ label: 'Unit pengundang', value: m.inviting_unit || '—' },
		{ label: 'Narahubung', value: m.contact_person || '—' },
		{ label: 'Penyelenggara', value: displayName(m.organizer) },
		// Times above are on your clock. If the organizer set this up in another zone,
		// show how it reads on theirs — that's the time on the invitation letter.
		...(m.timezone !== viewerTimezone()
			? [{ label: 'Waktu setempat penyelenggara', value: formatTimeIn(m.scheduled_start, m.timezone) }]
			: [])
	]);

	// Active participants first, people who dropped out at the bottom.
	const ORDER = { accepted: 0, pending: 1, declined: 2, cancelled: 3 } as const;
	const participants = $derived(
		[...m.participants].sort(
			(a, b) =>
				Number(b.role === 'organizer') - Number(a.role === 'organizer') ||
				ORDER[a.status] - ORDER[b.status]
		)
	);
	// Anyone with a live invitation — no point offering to invite them again.
	const activeIds = $derived(
		m.participants
			.filter((p) => p.status === 'pending' || p.status === 'accepted')
			.map((p) => p.user.id)
	);

	let error = $state('');
	let busy = $state(false);
	let inviting = $state(false);
	let removing = $state<Participant | null>(null);
	let confirmingCancel = $state(false);
	let confirmingDelete = $state(false);
	let responding = $state<{ meetingId: number; title: string; action: 'decline' | 'cancel' } | null>(
		null
	);

	async function call(url: string, init: RequestInit = {}): Promise<boolean> {
		busy = true;
		error = '';
		const res = await fetch(url, {
			...init,
			headers: init.body ? { 'Content-Type': 'application/json' } : undefined
		});
		busy = false;
		if (!res.ok) {
			error = await errorMessage(res);
			return false;
		}
		await invalidateAll();
		return true;
	}

	// The dialog stays open so several people can be invited in a row; the error, if
	// any, shows inside it.
	async function invite(user: UserBrief) {
		await call(`/api/meetings/${m.id}/participants`, {
			method: 'POST',
			body: JSON.stringify({ user_ids: [user.id] })
		});
	}

	async function accept() {
		await call(`/api/meetings/${m.id}/respond`, {
			method: 'POST',
			body: JSON.stringify({ action: 'accept' })
		});
	}

	async function confirmRemove() {
		if (!removing) return;
		await call(`/api/meetings/${m.id}/participants/${removing.user.id}`, { method: 'DELETE' });
		removing = null;
	}

	async function confirmCancelMeeting() {
		await call(`/api/meetings/${m.id}/cancel`, { method: 'POST' });
		confirmingCancel = false;
	}

	async function confirmDeleteMeeting() {
		busy = true;
		await fetch(`/api/meetings/${m.id}`, { method: 'DELETE' });
		busy = false;
		await goto('/dashboard/meetings');
		await invalidateAll();
	}

	async function setPay(hasPay: boolean, paid: boolean) {
		await call(`/api/meetings/${m.id}/my-pay`, {
			method: 'PUT',
			body: JSON.stringify({ has_takehome_pay: hasPay, takehome_pay_paid: hasPay && paid })
		});
	}

	function statusVariant(p: Participant) {
		if (p.status === 'accepted') return 'default' as const;
		if (p.status === 'pending') return 'secondary' as const;
		return 'outline' as const;
	}
</script>

<svelte:head>
	<title>{m.title} — SITUNG</title>
</svelte:head>

<SiteHeader title="Detail rapat" />
<div class="flex flex-1 flex-col p-4 md:p-6">
	<div class="mx-auto flex w-full max-w-5xl flex-col gap-6">
		<div class="flex flex-wrap items-center justify-between gap-3">
			<a href="/dashboard/meetings" class="text-xs text-muted-foreground hover:text-foreground">
				&larr; Rapat saya
			</a>
			{#if isOrganizer}
				<div class="flex flex-wrap items-center gap-2">
					{#if isScheduled}
						<Button variant="outline" size="sm" onclick={() => (confirmingCancel = true)}>
							Batalkan rapat
						</Button>
					{/if}
					<Button
						variant="outline"
						size="sm"
						class="text-destructive hover:text-destructive"
						onclick={() => (confirmingDelete = true)}
					>
						Hapus
					</Button>
					<Button href="/dashboard/meetings/{m.id}/edit" size="sm">Ubah</Button>
				</div>
			{/if}
		</div>

		{#if m.me.status === 'pending' && isScheduled}
			<div
				class="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-primary/30 bg-primary/5 p-4"
			>
				<div>
					<p class="font-medium">{displayName(m.organizer)} mengundang Anda ke rapat ini.</p>
					<p class="text-sm text-muted-foreground">
						Jika diterima, rapat masuk ke kalender Anda dan jam tersebut tercatat sibuk.
					</p>
				</div>
				<div class="flex gap-2">
					<Button
						variant="outline"
						disabled={busy}
						onclick={() => (responding = { meetingId: m.id, title: m.title, action: 'decline' })}
					>
						Tolak
					</Button>
					<Button disabled={busy} onclick={accept}>Terima</Button>
				</div>
			</div>
		{/if}

		{#if error}
			<p class="rounded-xl border border-destructive/40 bg-destructive/5 p-3 text-sm text-destructive">
				{error}
			</p>
		{/if}

		<div class="grid gap-6 lg:grid-cols-[1fr_340px]">
			<div class="min-w-0">
				<div class="flex flex-wrap items-center gap-2">
					<MeetingBadges meeting={m} />
					<Badge variant="outline">{LOCATION_TYPE_LABEL[m.location_type]}</Badge>
					<Badge variant="outline">{hasRun ? 'Sudah dilaksanakan' : 'Belum dilaksanakan'}</Badge>
				</div>

				<h1
					class="mt-3 font-heading text-3xl font-semibold tracking-tight sm:text-4xl {m.status ===
					'cancelled'
						? 'text-muted-foreground line-through'
						: ''}"
				>
					{m.title}
				</h1>

				<dl class="mt-8 grid gap-x-6 gap-y-4 sm:grid-cols-2">
					{#each details as detail (detail.label)}
						<div>
							<dt class="text-xs font-medium tracking-wide text-muted-foreground uppercase">
								{detail.label}
							</dt>
							<dd class="mt-0.5 text-sm">{detail.value}</dd>
						</div>
					{/each}
				</dl>

				{#if m.categories.length > 0}
					<div class="mt-6 flex flex-wrap gap-1.5">
						{#each m.categories as category (category)}
							<Badge variant="outline">{category}</Badge>
						{/each}
					</div>
				{/if}

				<Separator class="my-8" />

				<h2 class="mb-4 text-sm font-medium">Catatan</h2>
				{#key m.id + m.updated_at}
					<NoteContentView content={m.notes} />
				{/key}
			</div>

			<div class="flex flex-col gap-4">
				<Card.Root>
					<Card.Header>
						<Card.Title>Peserta</Card.Title>
						<Card.Description>
							{m.accepted_count} hadir{m.pending_count ? ` · ${m.pending_count} belum menjawab` : ''}
						</Card.Description>
						{#if isOrganizer && isScheduled}
							<Card.Action>
								<Button size="sm" variant="outline" onclick={() => (inviting = true)}>Undang</Button>
							</Card.Action>
						{/if}
					</Card.Header>
					<Card.Content>
						<ul class="flex flex-col gap-3">
							{#each participants as p (p.user.id)}
								<li class="flex items-start gap-3">
									<Avatar.Root class="size-8">
										<Avatar.Fallback class="text-xs">{initials(p.user)}</Avatar.Fallback>
									</Avatar.Root>
									<div class="min-w-0 flex-1">
										<p class="truncate text-sm font-medium">{displayName(p.user)}</p>
										<p class="truncate text-xs text-muted-foreground">
											{[p.user.position, p.user.unit_name].filter(Boolean).join(' · ') || p.user.email}
										</p>
										<div class="mt-1 flex flex-wrap items-center gap-1">
											{#if p.role === 'organizer'}
												<Badge>Penyelenggara</Badge>
											{:else}
												<Badge variant={statusVariant(p)}>{PARTICIPANT_STATUS_LABEL[p.status]}</Badge>
											{/if}
										</div>
										{#if p.response_note}
											<p class="mt-1 text-xs text-muted-foreground italic">"{p.response_note}"</p>
										{/if}
									</div>
									{#if isOrganizer && p.role !== 'organizer'}
										<Button
											variant="ghost"
											size="xs"
											class="text-muted-foreground"
											onclick={() => (removing = p)}
										>
											Keluarkan
										</Button>
									{/if}
								</li>
							{/each}
						</ul>
					</Card.Content>
				</Card.Root>

				{#if m.me.status === 'accepted'}
					<Card.Root>
						<Card.Header>
							<Card.Title>Honorarium saya</Card.Title>
							<Card.Description>Hanya Anda yang dapat melihat dan mengubahnya.</Card.Description>
						</Card.Header>
						<Card.Content class="flex flex-col gap-3">
							<div class="flex items-center gap-2">
								<Checkbox
									id="my-has-pay"
									checked={m.me.has_takehome_pay}
									disabled={busy}
									onCheckedChange={(v) => setPay(v === true, m.me.takehome_pay_paid)}
								/>
								<Label for="my-has-pay" class="text-sm font-normal">Rapat ini ada honorarium</Label>
							</div>
							<div class="flex items-center gap-2">
								<Checkbox
									id="my-pay-paid"
									checked={m.me.takehome_pay_paid}
									disabled={busy || !m.me.has_takehome_pay}
									onCheckedChange={(v) => setPay(true, v === true)}
								/>
								<Label
									for="my-pay-paid"
									class="text-sm font-normal {m.me.has_takehome_pay ? '' : 'text-muted-foreground'}"
								>
									Sudah dibayar
								</Label>
							</div>
						</Card.Content>
					</Card.Root>

					{#if !isOrganizer && isScheduled}
						<Button
							variant="outline"
							class="text-destructive hover:text-destructive"
							onclick={() => (responding = { meetingId: m.id, title: m.title, action: 'cancel' })}
						>
							Saya batal hadir
						</Button>
					{/if}
				{/if}
			</div>
		</div>
	</div>
</div>

<RespondDialog bind:target={responding} />

<Dialog.Root bind:open={inviting}>
	<Dialog.Content class="sm:max-w-xl">
		<Dialog.Header>
			<Dialog.Title>Undang peserta</Dialog.Title>
			<Dialog.Description>
				{m.scheduled_end
					? formatRange(m.scheduled_start, m.scheduled_end)
					: `${formatMeetingDateTime(m.scheduled_start)} (sampai akhir hari)`}. Hanya pegawai yang
				tersedia pada waktu tersebut yang dapat diundang.
			</Dialog.Description>
		</Dialog.Header>
		{#if error}
			<p class="text-sm text-destructive">{error}</p>
		{/if}
		<PeoplePicker
			start={toDateTimeInput(m.scheduled_start)}
			end={toDateTimeInput(m.scheduled_end)}
			units={data.units}
			excludeMeetingId={m.id}
			pickedIds={activeIds}
			onpick={invite}
		/>
	</Dialog.Content>
</Dialog.Root>

<AlertDialog.Root open={removing !== null} onOpenChange={(open) => !open && (removing = null)}>
	<AlertDialog.Content>
		<AlertDialog.Header>
			<AlertDialog.Title>Keluarkan {removing ? displayName(removing.user) : ''}?</AlertDialog.Title>
			<AlertDialog.Description>
				Yang bersangkutan akan diberi tahu dan rapat hilang dari kalendernya. Anda dapat
				mengundangnya lagi nanti.
			</AlertDialog.Description>
		</AlertDialog.Header>
		<AlertDialog.Footer>
			<AlertDialog.Cancel>Tidak jadi</AlertDialog.Cancel>
			<AlertDialog.Action disabled={busy} onclick={confirmRemove}>Keluarkan</AlertDialog.Action>
		</AlertDialog.Footer>
	</AlertDialog.Content>
</AlertDialog.Root>

<AlertDialog.Root bind:open={confirmingCancel}>
	<AlertDialog.Content>
		<AlertDialog.Header>
			<AlertDialog.Title>Batalkan rapat ini?</AlertDialog.Title>
			<AlertDialog.Description>
				Semua peserta akan diberi tahu dan jadwal mereka kembali kosong. Rapat tetap tercatat di
				daftar dengan tanda dibatalkan.
			</AlertDialog.Description>
		</AlertDialog.Header>
		<AlertDialog.Footer>
			<AlertDialog.Cancel>Tidak jadi</AlertDialog.Cancel>
			<AlertDialog.Action disabled={busy} onclick={confirmCancelMeeting}>Batalkan rapat</AlertDialog.Action>
		</AlertDialog.Footer>
	</AlertDialog.Content>
</AlertDialog.Root>

<AlertDialog.Root bind:open={confirmingDelete}>
	<AlertDialog.Content>
		<AlertDialog.Header>
			<AlertDialog.Title>Hapus rapat ini?</AlertDialog.Title>
			<AlertDialog.Description>
				Tindakan ini tidak dapat dibatalkan. Peserta yang masih diundang akan diberi tahu bahwa
				rapat dibatalkan.
			</AlertDialog.Description>
		</AlertDialog.Header>
		<AlertDialog.Footer>
			<AlertDialog.Cancel>Tidak jadi</AlertDialog.Cancel>
			<AlertDialog.Action disabled={busy} onclick={confirmDeleteMeeting}>
				{busy ? 'Menghapus...' : 'Hapus'}
			</AlertDialog.Action>
		</AlertDialog.Footer>
	</AlertDialog.Content>
</AlertDialog.Root>
