<script lang="ts">
	import { invalidateAll } from '$app/navigation';
	import * as Dialog from '$lib/components/ui/dialog/index.js';
	import { Button } from '$lib/components/ui/button/index.js';
	import { Label } from '$lib/components/ui/label/index.js';
	import { Textarea } from '$lib/components/ui/textarea/index.js';
	import { errorMessage } from '$lib/utils/http';

	/**
	 * Declining an invitation, or pulling out of one already accepted. Both tell the
	 * organizer, so both offer a place to say why.
	 */
	let {
		target = $bindable(null)
	}: {
		target: { meetingId: number; title: string; action: 'decline' | 'cancel' } | null;
	} = $props();

	let note = $state('');
	let submitting = $state(false);
	let error = $state('');

	const copy = $derived(
		target?.action === 'cancel'
			? {
					title: 'Batalkan kehadiran?',
					description: `Anda sudah menerima undangan rapat "${target.title}". Penyelenggara akan diberi tahu bahwa Anda batal hadir.`,
					confirm: 'Batalkan kehadiran'
				}
			: {
					title: 'Tolak undangan ini?',
					description: `Penyelenggara rapat "${target?.title}" akan diberi tahu bahwa Anda tidak dapat hadir.`,
					confirm: 'Tolak'
				}
	);

	async function submit() {
		if (!target) return;
		submitting = true;
		error = '';
		const res = await fetch(`/api/meetings/${target.meetingId}/respond`, {
			method: 'POST',
			headers: { 'Content-Type': 'application/json' },
			body: JSON.stringify({ action: target.action, note: note.trim() || null })
		});
		submitting = false;
		if (!res.ok) {
			error = await errorMessage(res);
			return;
		}
		target = null;
		note = '';
		await invalidateAll();
	}
</script>

<Dialog.Root
	open={target !== null}
	onOpenChange={(open) => {
		if (!open) {
			target = null;
			error = '';
		}
	}}
>
	<Dialog.Content>
		<Dialog.Header>
			<Dialog.Title>{copy.title}</Dialog.Title>
			<Dialog.Description>{copy.description}</Dialog.Description>
		</Dialog.Header>
		<div class="flex flex-col gap-1.5">
			<Label for="respond-note">Alasan (opsional)</Label>
			<Textarea id="respond-note" bind:value={note} placeholder="mis. Dinas luar kota" maxlength={500} />
		</div>
		{#if error}
			<p class="text-sm text-destructive">{error}</p>
		{/if}
		<Dialog.Footer>
			<Button variant="outline" onclick={() => (target = null)}>Tidak jadi</Button>
			<Button variant="destructive" disabled={submitting} onclick={submit}>
				{submitting ? 'Mengirim...' : copy.confirm}
			</Button>
		</Dialog.Footer>
	</Dialog.Content>
</Dialog.Root>
