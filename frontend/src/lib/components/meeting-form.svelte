<script lang="ts">
	import { untrack } from 'svelte';
	import { goto, invalidateAll } from '$app/navigation';
	import { HugeiconsIcon } from '@hugeicons/svelte';
	import { Cancel01Icon } from '@hugeicons/core-free-icons';
	import { Button } from '$lib/components/ui/button/index.js';
	import { Input } from '$lib/components/ui/input/index.js';
	import { Label } from '$lib/components/ui/label/index.js';
	import { Checkbox } from '$lib/components/ui/checkbox/index.js';
	import { Switch } from '$lib/components/ui/switch/index.js';
	import * as Select from '$lib/components/ui/select/index.js';
	import * as Card from '$lib/components/ui/card/index.js';
	import RichTextEditor from '$lib/components/editor/rich-text-editor.svelte';
	import { EMPTY_DOC } from '$lib/components/editor/empty-doc.js';
	import PeoplePicker from './people-picker.svelte';
	import { fetchAvailability } from '$lib/types/availability';
	import {
		fromDateTimeInput,
		toDateTimeInput,
		viewerTimezone,
		zoneLabel,
		LOCATION_TYPE_LABEL,
		type Meeting,
		type MeetingLocationType
	} from '$lib/types/meeting';
	import { displayName, type Unit, type UserBrief } from '$lib/types/user';
	import { errorMessage } from '$lib/utils/http';

	let {
		mode,
		meeting,
		categories = [],
		invitingUnits = [],
		units = [],
		defaultStart = '',
		defaultEnd = ''
	}: {
		mode: 'create' | 'edit';
		meeting?: Meeting;
		categories?: string[];
		/** Suggestions for the free-text "inviting unit" field. */
		invitingUnits?: string[];
		/** The organisation's units, for the invite picker's filter. */
		units?: Unit[];
		/** Prefilled when arriving from a cleared availability check. */
		defaultStart?: string;
		defaultEnd?: string;
	} = $props();

	// The edit page remounts this component (via {#key meeting.id}) whenever `meeting`
	// changes, so these only need its value at mount time.
	let title = $state(untrack(() => meeting?.title ?? ''));
	let scheduledStart = $state(
		untrack(() => toDateTimeInput(meeting?.scheduled_start ?? null) || defaultStart)
	);
	let scheduledEnd = $state(
		untrack(() => toDateTimeInput(meeting?.scheduled_end ?? null) || defaultEnd)
	);
	let actualStart = $state(untrack(() => toDateTimeInput(meeting?.actual_start ?? null)));
	let actualEnd = $state(untrack(() => toDateTimeInput(meeting?.actual_end ?? null)));
	let locationType = $state<MeetingLocationType>(untrack(() => meeting?.location_type ?? 'online'));
	let locationPlace = $state(untrack(() => meeting?.location_place ?? ''));
	let locationCity = $state(untrack(() => meeting?.location_city ?? ''));
	let contactPerson = $state(untrack(() => meeting?.contact_person ?? ''));
	let invitingUnit = $state(untrack(() => meeting?.inviting_unit ?? ''));
	let isFormal = $state(untrack(() => meeting?.is_formal ?? true));
	let categoriesInput = $state(untrack(() => meeting?.categories.join(', ') ?? ''));
	let hasTakehomePay = $state(untrack(() => meeting?.me.has_takehome_pay ?? false));
	let takehomePayPaid = $state(untrack(() => meeting?.me.takehome_pay_paid ?? false));
	let notes = $state<object>(
		untrack(() => (meeting?.notes && 'type' in meeting.notes ? meeting.notes : EMPTY_DOC))
	);

	// People to invite once the meeting is created (create mode only).
	let invitees = $state<UserBrief[]>([]);
	// Invitees who stopped being free after the time changed.
	let busyInviteeIds = $state<number[]>([]);

	// "Paid" is meaningless without an honorarium to pay, and the API rejects that pair.
	$effect(() => {
		if (!hasTakehomePay) takehomePayPaid = false;
	});

	// Someone added while the slot was free may clash once the time moves — recheck them.
	$effect(() => {
		const ids = invitees.map((u) => u.id);
		const start = scheduledStart;
		const end = scheduledEnd;
		if (!start || ids.length === 0) {
			busyInviteeIds = [];
			return;
		}
		const timer = setTimeout(async () => {
			try {
				const res = await fetchAvailability({ start, end: end || undefined, userIds: ids });
				busyInviteeIds = res.users.filter((u) => !u.available).map((u) => u.user.id);
			} catch {
				busyInviteeIds = [];
			}
		}, 300);
		return () => clearTimeout(timer);
	});

	let saving = $state(false);
	let error = $state('');

	const isOffline = $derived(locationType === 'offline');

	async function save() {
		if (!title.trim()) {
			error = 'Judul rapat wajib diisi.';
			return;
		}
		if (!scheduledStart) {
			error = 'Waktu mulai wajib diisi.';
			return;
		}

		saving = true;
		error = '';

		const payload = {
			title,
			scheduled_start: fromDateTimeInput(scheduledStart),
			scheduled_end: fromDateTimeInput(scheduledEnd),
			actual_start: fromDateTimeInput(actualStart),
			actual_end: fromDateTimeInput(actualEnd),
			location_type: locationType,
			// Cleared when online: the API rejects an online meeting that also has a venue.
			location_place: isOffline ? locationPlace.trim() || null : null,
			location_city: isOffline ? locationCity.trim() || null : null,
			contact_person: contactPerson.trim() || null,
			inviting_unit: invitingUnit.trim() || null,
			is_formal: isFormal,
			categories: categoriesInput
				.split(',')
				.map((c) => c.trim())
				.filter(Boolean),
			has_takehome_pay: hasTakehomePay,
			takehome_pay_paid: takehomePayPaid,
			notes,
			// Where the organizer is now — defines the meeting's "day" for a missing end time.
			timezone: viewerTimezone(),
			...(mode === 'create' ? { invitee_ids: invitees.map((u) => u.id) } : {})
		};

		const res =
			mode === 'create'
				? await fetch('/api/meetings', {
						method: 'POST',
						headers: { 'Content-Type': 'application/json' },
						body: JSON.stringify(payload)
					})
				: await fetch(`/api/meetings/${meeting!.id}`, {
						method: 'PUT',
						headers: { 'Content-Type': 'application/json' },
						body: JSON.stringify(payload)
					});

		saving = false;

		if (!res.ok) {
			// The API explains exactly which fields contradict each other, or who is
			// busy — surface that rather than a generic failure.
			error = await errorMessage(res, 'Rapat tidak dapat disimpan. Silakan coba lagi.');
			return;
		}

		const saved: Meeting = await res.json();
		await goto(`/dashboard/meetings/${saved.id}`);
		await invalidateAll();
	}
</script>

<div class="flex flex-1 flex-col gap-6 p-4 md:p-6">
	<div class="flex flex-wrap items-center justify-between gap-3">
		<div>
			<h2 class="font-heading text-lg font-semibold">
				{mode === 'create' ? 'Rapat baru' : 'Ubah rapat'}
			</h2>
			{#if mode === 'edit' && meeting && meeting.accepted_count + meeting.pending_count > 1}
				<p class="text-sm text-muted-foreground">
					Peserta akan diberi tahu jika Anda mengubah judul, waktu, atau lokasi.
				</p>
			{/if}
		</div>
		<div class="flex items-center gap-2">
			<Button
				variant="outline"
				href={mode === 'edit' ? `/dashboard/meetings/${meeting!.id}` : '/dashboard/meetings'}
			>
				Batal
			</Button>
			<Button onclick={save} disabled={saving}>{saving ? 'Menyimpan...' : 'Simpan'}</Button>
		</div>
	</div>

	{#if error}
		<p class="rounded-xl border border-destructive/40 bg-destructive/5 p-3 text-sm text-destructive">
			{error}
		</p>
	{/if}

	<div class="grid gap-6 lg:grid-cols-[1fr_340px]">
		<div class="flex min-w-0 flex-col gap-6">
			<Input
				bind:value={title}
				placeholder="Judul rapat"
				class="h-auto py-3 font-heading text-2xl font-semibold md:text-2xl"
			/>

			{#if mode === 'create'}
				<Card.Root>
					<Card.Header>
						<Card.Title>Undang peserta</Card.Title>
						<Card.Description>
							Hanya pegawai yang tersedia pada waktu rapat yang dapat diundang. Mereka akan
							menerima notifikasi dan dapat menerima atau menolak.
						</Card.Description>
					</Card.Header>
					<Card.Content class="flex flex-col gap-4">
						{#if invitees.length > 0}
							<div class="flex flex-wrap gap-2">
								{#each invitees as u (u.id)}
									{@const busy = busyInviteeIds.includes(u.id)}
									<span
										class="inline-flex items-center gap-1.5 rounded-full border py-1 ps-3 pe-1 text-xs {busy
											? 'border-destructive/50 text-destructive'
											: ''}"
										title={busy ? 'Sudah tidak tersedia pada waktu ini' : undefined}
									>
										{displayName(u)}{busy ? ' · sibuk' : ''}
										<button
											type="button"
											class="rounded-full p-0.5 hover:bg-muted"
											aria-label="Hapus {displayName(u)}"
											onclick={() => (invitees = invitees.filter((x) => x.id !== u.id))}
										>
											<HugeiconsIcon icon={Cancel01Icon} strokeWidth={2} class="size-3" />
										</button>
									</span>
								{/each}
							</div>
						{/if}
						<PeoplePicker
							start={scheduledStart}
							end={scheduledEnd}
							{units}
							pickedIds={invitees.map((u) => u.id)}
							pickLabel="Tambah"
							onpick={(u) => {
								invitees = [...invitees, u];
							}}
						/>
					</Card.Content>
				</Card.Root>
			{/if}

			<div class="flex flex-col gap-2">
				<div>
					<h3 class="text-sm font-medium">Catatan</h3>
					<p class="text-xs text-muted-foreground">
						Agenda, keputusan, tindak lanjut — apa pun yang perlu dicatat. Peserta dapat membacanya.
					</p>
				</div>
				<div class="rounded-xl border p-4">
					<RichTextEditor
						initialContent={meeting?.notes ?? {}}
						onUpdate={(json) => (notes = json)}
						placeholder="Apa yang dibahas?"
					/>
				</div>
			</div>
		</div>

		<div class="flex flex-col gap-4">
			<div class="flex flex-col gap-3 rounded-xl border p-4">
				<h3 class="text-xs font-medium tracking-wide text-muted-foreground uppercase">Jadwal ({zoneLabel()})</h3>
				<div class="flex flex-col gap-1.5">
					<Label for="sched-start" class="text-xs text-muted-foreground">Mulai</Label>
					<Input id="sched-start" type="datetime-local" bind:value={scheduledStart} />
				</div>
				<div class="flex flex-col gap-1.5">
					<Label for="sched-end" class="text-xs text-muted-foreground">Selesai</Label>
					<Input id="sched-end" type="datetime-local" bind:value={scheduledEnd} />
				</div>
				<div class="flex items-center justify-between gap-3 border-t pt-3">
					<div>
						<Label for="is-formal" class="text-xs font-medium">Rapat formal</Label>
						<p class="mt-0.5 text-xs text-muted-foreground">Membuat Anda berstatus sibuk pada jam tersebut</p>
					</div>
					<Switch id="is-formal" bind:checked={isFormal} />
				</div>
			</div>

			<div class="flex flex-col gap-3 rounded-xl border p-4">
				<h3 class="text-xs font-medium tracking-wide text-muted-foreground uppercase">
					Realisasi pelaksanaan ({zoneLabel()})
				</h3>
				<p class="text-xs text-muted-foreground">Kosongkan sampai rapat selesai dilaksanakan.</p>
				<div class="flex flex-col gap-1.5">
					<Label for="actual-start" class="text-xs text-muted-foreground">Mulai</Label>
					<Input id="actual-start" type="datetime-local" bind:value={actualStart} />
				</div>
				<div class="flex flex-col gap-1.5">
					<Label for="actual-end" class="text-xs text-muted-foreground">Selesai</Label>
					<Input id="actual-end" type="datetime-local" bind:value={actualEnd} />
				</div>
			</div>

			<div class="flex flex-col gap-3 rounded-xl border p-4">
				<h3 class="text-xs font-medium tracking-wide text-muted-foreground uppercase">Lokasi</h3>
				<Select.Root type="single" bind:value={locationType}>
					<Select.Trigger id="location-type" class="w-full">
						{LOCATION_TYPE_LABEL[locationType]}
					</Select.Trigger>
					<Select.Content>
						<Select.Item value="online">Daring</Select.Item>
						<Select.Item value="offline">Luring</Select.Item>
					</Select.Content>
				</Select.Root>

				{#if isOffline}
					<div class="flex flex-col gap-1.5">
						<Label for="place" class="text-xs text-muted-foreground">Tempat</Label>
						<Input id="place" bind:value={locationPlace} placeholder="Gedung Utama Lt. 3" />
					</div>
					<div class="flex flex-col gap-1.5">
						<Label for="city" class="text-xs text-muted-foreground">Kota</Label>
						<Input id="city" bind:value={locationCity} placeholder="Jakarta Pusat" />
					</div>
				{/if}
			</div>

			<div class="flex flex-col gap-3 rounded-xl border p-4">
				<h3 class="text-xs font-medium tracking-wide text-muted-foreground uppercase">
					Asal undangan
				</h3>
				<div class="flex flex-col gap-1.5">
					<Label for="unit" class="text-xs text-muted-foreground">Unit pengundang</Label>
					<Input id="unit" bind:value={invitingUnit} list="meeting-units" placeholder="Deputi Bidang..." />
					<datalist id="meeting-units">
						{#each invitingUnits as u (u)}
							<option value={u}></option>
						{/each}
					</datalist>
				</div>
				<div class="flex flex-col gap-1.5">
					<Label for="contact" class="text-xs text-muted-foreground">Narahubung</Label>
					<Input id="contact" bind:value={contactPerson} placeholder="Nama dan nomor yang dapat dihubungi" />
				</div>
				<div class="flex flex-col gap-1.5">
					<Label for="categories" class="text-xs text-muted-foreground">Jenis rapat</Label>
					<Input
						id="categories"
						bind:value={categoriesInput}
						list="meeting-categories"
						placeholder="rakor, sosialisasi, bimtek"
					/>
					<datalist id="meeting-categories">
						{#each categories as c (c)}
							<option value={c}></option>
						{/each}
					</datalist>
					<p class="text-xs text-muted-foreground">Pisahkan dengan koma</p>
				</div>
			</div>

			<div class="flex flex-col gap-3 rounded-xl border p-4">
				<div>
					<h3 class="text-xs font-medium tracking-wide text-muted-foreground uppercase">
						Honorarium saya
					</h3>
					<p class="mt-0.5 text-xs text-muted-foreground">
						Hanya milik Anda — setiap peserta mencatat honorariumnya sendiri.
					</p>
				</div>
				<div class="flex items-center gap-2">
					<Checkbox id="has-pay" bind:checked={hasTakehomePay} />
					<Label for="has-pay" class="text-sm font-normal">Rapat ini ada honorarium</Label>
				</div>
				<div class="flex items-center gap-2">
					<Checkbox id="pay-paid" bind:checked={takehomePayPaid} disabled={!hasTakehomePay} />
					<Label
						for="pay-paid"
						class="text-sm font-normal {hasTakehomePay ? '' : 'text-muted-foreground'}"
					>
						Sudah dibayar
					</Label>
				</div>
			</div>
		</div>
	</div>
</div>
