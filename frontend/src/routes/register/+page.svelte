<script lang="ts">
	import AuthShell from '$lib/components/auth-shell.svelte';
	import RegisterForm from '$lib/components/register-form.svelte';
	import { APP_NAME } from '$lib/config.js';
	import type { PageProps } from './$types';

	let { form }: PageProps = $props();
</script>

<svelte:head>
	<title>Penyiapan — {APP_NAME}</title>
</svelte:head>

<AuthShell>
	<RegisterForm {form} />
</AuthShell>
