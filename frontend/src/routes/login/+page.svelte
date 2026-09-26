<script lang="ts">
	import AuthShell from '$lib/components/auth-shell.svelte';
	import LoginForm from '$lib/components/login-form.svelte';
	import { APP_NAME } from '$lib/config.js';
	import type { PageProps } from './$types';

	let { form }: PageProps = $props();
</script>

<svelte:head>
	<title>Masuk — {APP_NAME}</title>
</svelte:head>

<AuthShell>
	<LoginForm {form} />
</AuthShell>
