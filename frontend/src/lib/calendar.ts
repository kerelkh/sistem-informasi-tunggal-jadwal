/**
 * Calendar maths on the viewer's local wall-clock strings ("YYYY-MM-DD" /
 * "YYYY-MM-DDTHH:mm"). Meetings arrive as instants and are placed on the viewer's
 * own clock, so the same meeting sits in the 09.00 row in Jakarta and the 10.00 row
 * in Makassar. After that conversion it's plain calendar arithmetic on the strings.
 */
import {
	addDays,
	isPendingInvitation,
	MONTHS,
	nowLocal,
	toLocalWall,
	weekdayOf,
	type MeetingListItem
} from '$lib/types/meeting';

export type CalendarView = 'month' | 'week';

/** How the meeting relates to me — drives its colour on the calendar. */
export type EventKind = 'organizer' | 'attending' | 'pending';

export interface CalendarEvent {
	meeting: MeetingListItem;
	kind: EventKind;
	/** "YYYY-MM-DDTHH:mm" on the viewer's clock. */
	start: string;
	end: string | null;
	cancelled: boolean;
}

export const WEEKDAY_SHORT = ['Sen', 'Sel', 'Rab', 'Kam', 'Jum', 'Sab', 'Min'];

export function todayLocal(): string {
	return nowLocal().slice(0, 10);
}

/** The Monday on or before `date` — Indonesian calendars start the week on Senin. */
export function startOfWeek(date: string): string {
	const offset = (weekdayOf(date) + 6) % 7; // Monday → 0 … Sunday → 6
	return addDays(date, -offset);
}

export function weekDays(anchor: string): string[] {
	const monday = startOfWeek(anchor);
	return Array.from({ length: 7 }, (_, i) => addDays(monday, i));
}

/** Whole weeks (Monday–Sunday) covering the anchor's month. */
export function monthGrid(anchor: string): string[][] {
	const first = `${anchor.slice(0, 7)}-01`;
	const weeks: string[][] = [];
	let day = startOfWeek(first);
	do {
		weeks.push(Array.from({ length: 7 }, (_, i) => addDays(day, i)));
		day = addDays(day, 7);
	} while (day.slice(0, 7) === anchor.slice(0, 7));
	return weeks;
}

export function shiftMonth(anchor: string, months: number): string {
	const [y, m] = anchor.split('-').map(Number);
	const total = y * 12 + (m - 1) + months;
	return `${Math.floor(total / 12)}-${String((total % 12) + 1).padStart(2, '0')}-01`;
}

export function monthTitle(anchor: string): string {
	const [y, m] = anchor.split('-').map(Number);
	return `${MONTHS[m - 1]} ${y}`;
}

/** "21 – 27 September 2026", or "29 September – 5 Oktober 2026" across a month boundary. */
export function weekTitle(anchor: string): string {
	const days = weekDays(anchor);
	const [y1, m1, d1] = days[0].split('-').map(Number);
	const [y2, m2, d2] = days[6].split('-').map(Number);
	if (y1 !== y2) return `${d1} ${MONTHS[m1 - 1]} ${y1} – ${d2} ${MONTHS[m2 - 1]} ${y2}`;
	if (m1 !== m2) return `${d1} ${MONTHS[m1 - 1]} – ${d2} ${MONTHS[m2 - 1]} ${y2}`;
	return `${d1} – ${d2} ${MONTHS[m2 - 1]} ${y2}`;
}

/**
 * The meetings that belong on my calendar: the ones I organise or accepted, plus
 * invitations still waiting for an answer (shown tentatively). Declined and
 * withdrawn ones are left off — I'm not going.
 */
export function toEvents(meetings: MeetingListItem[], includePending: boolean): CalendarEvent[] {
	return meetings
		.filter((m) => m.me.status === 'accepted' || (includePending && isPendingInvitation(m)))
		.map((m) => ({
			meeting: m,
			kind:
				m.me.status === 'pending' ? 'pending' : m.me.role === 'organizer' ? 'organizer' : 'attending',
			start: toLocalWall(m.scheduled_start),
			end: m.scheduled_end ? toLocalWall(m.scheduled_end) : null,
			cancelled: m.status === 'cancelled'
		}));
}

/** Events grouped by the day they start on, each day sorted by start time. */
export function byDay(events: CalendarEvent[]): Map<string, CalendarEvent[]> {
	const map = new Map<string, CalendarEvent[]>();
	for (const e of [...events].sort((a, b) => a.start.localeCompare(b.start))) {
		const day = e.start.slice(0, 10);
		map.set(day, [...(map.get(day) ?? []), e]);
	}
	return map;
}

export function minutesOf(wall: string): number {
	return Number(wall.slice(11, 13)) * 60 + Number(wall.slice(14, 16));
}

/** Minutes past midnight at which the event stops occupying its start day. */
export function endMinutesOnDay(e: CalendarEvent): number {
	// No end time: drawn as one hour, flagged in the UI. (Availability is stricter and
	// treats it as the whole day — the calendar just needs somewhere to put it.)
	if (!e.end) return Math.min(minutesOf(e.start) + 60, 24 * 60);
	if (e.end.slice(0, 10) !== e.start.slice(0, 10)) return 24 * 60;
	return Math.max(minutesOf(e.end), minutesOf(e.start) + 15);
}

export interface PositionedEvent {
	event: CalendarEvent;
	startMin: number;
	endMin: number;
	/** Column within its cluster of overlapping events, and how many columns the cluster has. */
	lane: number;
	lanes: number;
}

/**
 * Side-by-side layout for one day's events: overlapping events split the width
 * between them, the way paper diaries do it.
 */
export function layoutDay(events: CalendarEvent[]): PositionedEvent[] {
	const items = events
		.map((event) => ({ event, startMin: minutesOf(event.start), endMin: endMinutesOnDay(event), lane: 0, lanes: 1 }))
		.sort((a, b) => a.startMin - b.startMin || b.endMin - a.endMin);

	let cluster: PositionedEvent[] = [];
	let clusterEnd = -1;
	const laneEnds: number[] = [];

	const closeCluster = () => {
		const lanes = Math.max(1, ...cluster.map((c) => c.lane + 1));
		for (const c of cluster) c.lanes = lanes;
		cluster = [];
		laneEnds.length = 0;
	};

	for (const item of items) {
		if (item.startMin >= clusterEnd && cluster.length) closeCluster();
		let lane = laneEnds.findIndex((end) => end <= item.startMin);
		if (lane === -1) lane = laneEnds.length;
		laneEnds[lane] = item.endMin;
		item.lane = lane;
		cluster.push(item);
		clusterEnd = Math.max(clusterEnd, item.endMin);
	}
	if (cluster.length) closeCluster();
	return items;
}
