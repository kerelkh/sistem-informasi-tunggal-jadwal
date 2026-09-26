<script lang="ts">
	import { enhance } from '$app/forms';
	import * as Card from '$lib/components/ui/card/index.js';
	import { Button } from '$lib/components/ui/button/index.js';
	import { FieldGroup, Field, FieldLabel, FieldError } from '$lib/components/ui/field/index.js';
	import { Input } from '$lib/components/ui/input/index.js';

	let { form }: { form?: { error?: string; email?: string; fullName?: string } | null } = $props();

	const id = $props.id();
	let submitting = $state(false);
</script>

<Card.Root class="mx-auto w-full max-w-sm">
	<Card.Header>
		<Card.Title class="text-xl">Buat akun administrator</Card.Title>
		<Card.Description>
			Akun pertama ini mengelola unit kerja dan pengguna. Pengguna lain ditambahkan dari dalam aplikasi.
		</Card.Description>
	</Card.Header>
	<Card.Content>
		<form
			method="POST"
			use:enhance={() => {
				submitting = true;
				return async ({ update }) => {
					submitting = false;
					await update();
				};
			}}
		>
			<FieldGroup>
				<Field>
					<FieldLabel for="name-{id}">Nama lengkap</FieldLabel>
					<Input id="name-{id}" name="full_name" value={form?.fullName ?? ''} required />
				</Field>
				<Field>
					<FieldLabel for="email-{id}">Email</FieldLabel>
					<Input id="email-{id}" name="email" type="email" value={form?.email ?? ''} required />
				</Field>
				<Field>
					<FieldLabel for="password-{id}">Kata sandi</FieldLabel>
					<Input id="password-{id}" name="password" type="password" minlength={8} required />
				</Field>
				<Field>
					<FieldLabel for="confirm-{id}">Ulangi kata sandi</FieldLabel>
					<Input id="confirm-{id}" name="confirm" type="password" minlength={8} required />
				</Field>
				{#if form?.error}
					<FieldError>{form.error}</FieldError>
				{/if}
				<Field>
					<Button type="submit" class="w-full" disabled={submitting}>
						{submitting ? 'Membuat...' : 'Buat administrator'}
					</Button>
				</Field>
			</FieldGroup>
		</form>
	</Card.Content>
</Card.Root>
