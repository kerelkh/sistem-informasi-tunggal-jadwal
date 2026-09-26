<script lang="ts">
	import SiteHeader from '$lib/components/site-header.svelte';
	import MeetingForm from '$lib/components/meeting-form.svelte';
	import type { PageProps } from './$types';

	let { data }: PageProps = $props();
</script>

<svelte:head>
	<title>{data.meeting.title} — SITUNG</title>
</svelte:head>

<SiteHeader title="Ubah rapat" />
{#key data.meeting.id}
	<MeetingForm
		mode="edit"
		meeting={data.meeting}
		categories={data.categories}
		invitingUnits={data.invitingUnits}
	/>
{/key}
