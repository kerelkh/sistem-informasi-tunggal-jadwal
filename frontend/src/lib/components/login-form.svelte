<script lang="ts">
	import { enhance } from '$app/forms';
	import * as Card from '$lib/components/ui/card/index.js';
	import { Button } from '$lib/components/ui/button/index.js';
	import {
		FieldGroup,
		Field,
		FieldLabel,
		FieldDescription,
		FieldError
	} from '$lib/components/ui/field/index.js';
	import { Input } from '$lib/components/ui/input/index.js';

	let { form }: { form?: { error?: string; email?: string } | null } = $props();

	const id = $props.id();
	let submitting = $state(false);
</script>

<Card.Root class="mx-auto w-full max-w-sm">
	<Card.Header>
		<Card.Title class="text-xl">Masuk</Card.Title>
		<Card.Description>Gunakan akun yang diberikan oleh administrator.</Card.Description>
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
					<FieldLabel for="email-{id}">Email</FieldLabel>
					<Input
						id="email-{id}"
						name="email"
						type="email"
						autocomplete="username"
						value={form?.email ?? ''}
						required
					/>
				</Field>
				<Field>
					<FieldLabel for="password-{id}">Kata sandi</FieldLabel>
					<Input
						id="password-{id}"
						name="password"
						type="password"
						autocomplete="current-password"
						required
					/>
				</Field>
				{#if form?.error}
					<FieldError>{form.error}</FieldError>
				{/if}
				<Field>
					<Button type="submit" class="w-full" disabled={submitting}>
						{submitting ? 'Memproses...' : 'Masuk'}
					</Button>
					<FieldDescription class="text-center">
						Lupa kata sandi? Minta administrator untuk mengatur ulang.
					</FieldDescription>
				</Field>
			</FieldGroup>
		</form>
	</Card.Content>
</Card.Root>
