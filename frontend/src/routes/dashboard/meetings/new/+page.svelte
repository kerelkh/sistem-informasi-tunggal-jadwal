<script lang="ts">
	import SiteHeader from '$lib/components/site-header.svelte';
	import MeetingForm from '$lib/components/meeting-form.svelte';
	import { page } from '$app/state';
	import type { PageProps } from './$types';

	let { data }: PageProps = $props();

	const defaultStart = $derived(page.url.searchParams.get('start') ?? '');
	const defaultEnd = $derived(page.url.searchParams.get('end') ?? '');
</script>

<svelte:head>
	<title>Rapat baru — SITUNG</title>
</svelte:head>

<SiteHeader title="Rapat baru" />
<MeetingForm
	mode="create"
	categories={data.categories}
	invitingUnits={data.invitingUnits}
	units={data.units}
	{defaultStart}
	{defaultEnd}
/>
