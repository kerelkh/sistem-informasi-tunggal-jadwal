import type { UserBrief } from './user';

export type MeetingLocationType = 'online' | 'offline';
export type MeetingStatus = 'scheduled' | 'cancelled';
export type ParticipantRole = 'organizer' | 'invitee';
export type ParticipantStatus = 'pending' | 'accepted' | 'declined' | 'cancelled';

/** How a meeting relates to the person looking at it. */
export interface MyParticipation {
	role: ParticipantRole;
	status: ParticipantStatus;
	has_takehome_pay: boolean;
	takehome_pay_paid: boolean;
}

export interface MeetingListItem {
	id: number;
	title: string;
	scheduled_start: string;
	scheduled_end: string | null;
	actual_start: string | null;
	actual_end: string | null;
	location_type: MeetingLocationType;
	location_place: string | null;
	location_city: string | null;
	contact_person: string | null;
	inviting_unit: string | null;
	is_formal: boolean;
	categories: string[];
	/** The organizer's IANA zone — where the meeting's "day" is. */
	timezone: string;
	status: MeetingStatus;
	organizer: UserBrief;
	me: MyParticipation;
	accepted_count: number;
	pending_count: number;
}

export interface Participant {
	user: UserBrief;
	role: ParticipantRole;
	status: ParticipantStatus;
	response_note: string | null;
	invited_at: string;
	responded_at: string | null;
}

export interface Meeting extends MeetingListItem {
	notes: Record<string, unknown>;
	participants: Participant[];
	created_at: string;
	updated_at: string;
}

export const PARTICIPANT_STATUS_LABEL: Record<ParticipantStatus, string> = {
	pending: 'Menunggu jawaban',
	accepted: 'Hadir',
	declined: 'Menolak',
	cancelled: 'Batal hadir'
};

export const LOCATION_TYPE_LABEL: Record<MeetingLocationType, string> = {
	online: 'Daring',
	offline: 'Luring'
};

/** Whether the meeting (as it actually ran, else as scheduled) is still ahead. */
export function isUpcoming(m: MeetingListItem, nowMs = Date.now()): boolean {
	return Date.parse(effectiveStart(m)) >= nowMs;
}

/** On my calendar: I organise it, or I said yes. */
export function isOnMyCalendar(m: MeetingListItem): boolean {
	return m.me.status === 'accepted';
}

export function isPendingInvitation(m: MeetingListItem): boolean {
	return m.me.status === 'pending' && m.status === 'scheduled';
}

export function isOrganizer(m: MeetingListItem): boolean {
	return m.me.role === 'organizer';
}

/**
 * Times travel as instants — points on the global timeline, like a Unix timestamp —
 * and are shown on the viewer's own clock. A meeting at 02.00 UTC reads 09.00 in
 * Jakarta and 10.00 in Makassar; nobody's zone is the "real" one.
 *
 * Inside the UI we work in the viewer's local wall-clock strings
 * ("YYYY-MM-DDTHH:mm"): that's what `datetime-local` inputs, calendar grids and URL
 * params speak. Convert at the edges: `toLocalWall` coming from the API,
 * `fromDateTimeInput` going back.
 */

/** The viewer's IANA zone, e.g. "Asia/Jakarta" — sent with meetings they create. */
export function viewerTimezone(): string {
	return Intl.DateTimeFormat().resolvedOptions().timeZone || 'UTC';
}

const localWallFormat = new Intl.DateTimeFormat('en-CA', {
	year: 'numeric',
	month: '2-digit',
	day: '2-digit',
	hour: '2-digit',
	minute: '2-digit',
	hourCycle: 'h23'
});

function wallIn(format: Intl.DateTimeFormat, instant: string | Date): string {
	const d = typeof instant === 'string' ? new Date(instant) : instant;
	const p = Object.fromEntries(format.formatToParts(d).map((x) => [x.type, x.value]));
	return `${p.year}-${p.month}-${p.day}T${p.hour}:${p.minute}`;
}

/** An instant as "YYYY-MM-DDTHH:mm" on the viewer's clock. */
export function toLocalWall(instant: string | Date): string {
	return wallIn(localWallFormat, instant);
}

/** Now, on the viewer's clock. */
export function nowLocal(): string {
	return toLocalWall(new Date());
}

/** API instant → `datetime-local` value. */
export function toDateTimeInput(iso: string | null): string {
	return iso ? toLocalWall(iso) : '';
}

/**
 * `datetime-local` value → API instant. The browser reads a bare date-time as local
 * time, which is exactly what the viewer typed.
 */
export function fromDateTimeInput(value: string): string | null {
	return value ? new Date(value).toISOString() : null;
}

/** Moves a "YYYY-MM-DD..." string by whole calendar days. */
export function addDays(isoDate: string, days: number): string {
	const [y, m, d] = isoDate.slice(0, 10).split('-').map(Number);
	const moved = new Date(Date.UTC(y, m - 1, d + days));
	return moved.toISOString().slice(0, 10) + isoDate.slice(10);
}

/** Shifts a "YYYY-MM-DDTHH:mm" wall-clock string by minutes, as plain calendar arithmetic. */
export function addMinutes(wall: string, minutes: number): string {
	const [y, m, d] = wall.slice(0, 10).split('-').map(Number);
	const [hh, mm] = wall.slice(11, 16).split(':').map(Number);
	return new Date(Date.UTC(y, m - 1, d, hh, mm + minutes)).toISOString().slice(0, 16);
}

const MONTHS_SHORT = ['Jan', 'Feb', 'Mar', 'Apr', 'Mei', 'Jun', 'Jul', 'Agu', 'Sep', 'Okt', 'Nov', 'Des'];
export const MONTHS = [
	'Januari', 'Februari', 'Maret', 'April', 'Mei', 'Juni',
	'Juli', 'Agustus', 'September', 'Oktober', 'November', 'Desember'
];
export const WEEKDAYS = ['Minggu', 'Senin', 'Selasa', 'Rabu', 'Kamis', 'Jumat', 'Sabtu'];

/** Day of week for a "YYYY-MM-DD" date, 0 = Minggu. */
export function weekdayOf(isoDate: string): number {
	const [y, m, d] = isoDate.slice(0, 10).split('-').map(Number);
	return new Date(Date.UTC(y, m - 1, d)).getUTCDay();
}

/**
 * The viewer's zone as a short label at a given moment: "WIB", "WITA", "WIT" in
 * Indonesia, "GMT+1" / "CEST" elsewhere. Per instant, because of daylight saving.
 */
export function zoneLabel(instant: string | Date = new Date(), timeZone?: string): string {
	const d = typeof instant === 'string' ? new Date(instant) : instant;
	const part = new Intl.DateTimeFormat('id-ID', { timeZone, timeZoneName: 'short' })
		.formatToParts(d)
		.find((p) => p.type === 'timeZoneName');
	return part?.value ?? '';
}

/** "27 Sep 2026" for a local "YYYY-MM-DD..." string. */
export function formatWallDate(wall: string): string {
	const [y, m, d] = wall.slice(0, 10).split('-').map(Number);
	return `${d} ${MONTHS_SHORT[m - 1]} ${y}`;
}

/** "Sabtu, 26 September 2026" for a local "YYYY-MM-DD" string. */
export function formatLongDate(wall: string): string {
	const [y, m, d] = wall.slice(0, 10).split('-').map(Number);
	return `${WEEKDAYS[weekdayOf(wall)]}, ${d} ${MONTHS[m - 1]} ${y}`;
}

/** "13.30" for a local wall-clock string — Indonesian writes times with a dot. */
export function formatWallTime(wall: string): string {
	return wall.slice(11, 16).replace(':', '.');
}

/** "13.30" on the viewer's clock. */
export function formatTime(iso: string | null): string {
	return iso ? formatWallTime(toLocalWall(iso)) : '';
}

/** "27 Sep 2026, 13.30 WIB" on the viewer's clock. */
export function formatMeetingDateTime(iso: string | null): string {
	if (!iso) return '—';
	const wall = toLocalWall(iso);
	return `${formatWallDate(wall)}, ${formatWallTime(wall)} ${zoneLabel(iso)}`;
}

/** "27 Sep 2026, 13.30 – 15.00 WIB", collapsing the date when both ends share it. */
export function formatRange(start: string, end: string | null): string {
	if (!end) return formatMeetingDateTime(start);
	const s = toLocalWall(start);
	const e = toLocalWall(end);
	const label = zoneLabel(start);
	return s.slice(0, 10) === e.slice(0, 10)
		? `${formatWallDate(s)}, ${formatWallTime(s)} – ${formatWallTime(e)} ${label}`
		: `${formatWallDate(s)}, ${formatWallTime(s)} – ${formatWallDate(e)}, ${formatWallTime(e)} ${label}`;
}

/** "09.00 WIT" — how an instant reads on a clock in another zone (e.g. the organizer's). */
export function formatTimeIn(iso: string, timeZone: string): string {
	const wall = wallIn(
		new Intl.DateTimeFormat('en-CA', {
			timeZone,
			year: 'numeric',
			month: '2-digit',
			day: '2-digit',
			hour: '2-digit',
			minute: '2-digit',
			hourCycle: 'h23'
		}),
		iso
	);
	return `${formatWallDate(wall)}, ${formatWallTime(wall)} ${zoneLabel(iso, timeZone)}`;
}

export function locationLabel(m: MeetingListItem): string {
	if (m.location_type === 'online') return 'Daring';
	return [m.location_place, m.location_city].filter(Boolean).join(', ') || 'Luring';
}

/**
 * Which dates actually describe when a meeting sat in the day.
 *
 * A meeting that has run is defined by when it really happened — a rakor scheduled
 * for 09:00 that actually ran 09:20–11:45 occupied 09:20–11:45. Until it runs, the
 * schedule is the only thing we know, so that's what counts.
 */
export function effectiveStart(m: MeetingListItem): string {
	return m.actual_start ?? m.scheduled_start;
}

export function effectiveEnd(m: MeetingListItem): string | null {
	return m.actual_end ?? m.scheduled_end;
}

export function usesActualDates(m: MeetingListItem): boolean {
	return m.actual_start !== null;
}
