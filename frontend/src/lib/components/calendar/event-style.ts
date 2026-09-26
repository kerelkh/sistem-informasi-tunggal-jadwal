import type { CalendarEvent } from '$lib/calendar';

/** One colour language for both views, explained by the legend on the page. */
export function eventClasses(e: CalendarEvent): string {
	const base =
		e.kind === 'organizer'
			? 'bg-primary text-primary-foreground border-primary'
			: e.kind === 'attending'
				? 'bg-sky-500/15 text-sky-900 border-sky-500/40 dark:text-sky-100'
				: 'bg-background text-foreground border-dashed border-muted-foreground/60';
	return `${base} ${e.cancelled ? 'line-through opacity-50' : ''}`;
}
