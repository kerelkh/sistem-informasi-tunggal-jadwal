<script lang="ts">
	import { navigating } from '$app/state';
</script>

{#if navigating.to}
	<div class="fixed inset-x-0 top-0 z-100 h-0.5 overflow-hidden bg-primary/20">
		<div class="h-full w-1/3 animate-[nav-progress_1s_ease-in-out_infinite] bg-primary"></div>
	</div>
{/if}

<style>
	@keyframes nav-progress {
		0% {
			transform: translateX(-100%);
		}
		100% {
			transform: translateX(300%);
		}
	}
</style>
