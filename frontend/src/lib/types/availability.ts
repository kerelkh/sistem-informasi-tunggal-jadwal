import { errorMessage } from '$lib/utils/http';
import { fromDateTimeInput, viewerTimezone, type ParticipantStatus } from './meeting';
import type { UserBrief } from './user';

export interface BusySlot {
	meeting_id: number;
	title: string;
	scheduled_start: string;
	scheduled_end: string | null;
	is_formal: boolean;
	status: ParticipantStatus;
	/** No scheduled end, so it's assumed to run to the end of its day. */
	assumed_end: boolean;
	/** A formal meeting they've committed to — rules the slot out. */
	blocking: boolean;
	/** Invited but not answered yet. */
	tentative: boolean;
}

export interface UserAvailability {
	user: UserBrief;
	available: boolean;
	busy: BusySlot[];
}

export interface AvailabilityResult {
	window_start: string;
	window_end: string;
	users: UserAvailability[];
}

export interface AvailabilityQuery {
	/** Local wall-clock "YYYY-MM-DDTHH:mm", as the viewer typed it. */
	start: string;
	end?: string;
	q?: string;
	unitId?: number | null;
	userIds?: number[];
	excludeMeetingId?: number;
}

export async function fetchAvailability(query: AvailabilityQuery): Promise<AvailabilityResult> {
	// Sent as instants; `tz` makes a blank end mean "the rest of *my* day".
	const params = new URLSearchParams({
		start: fromDateTimeInput(query.start)!,
		tz: viewerTimezone()
	});
	if (query.end) params.set('end', fromDateTimeInput(query.end)!);
	if (query.q?.trim()) params.set('q', query.q.trim());
	if (query.unitId) params.set('unit_id', String(query.unitId));
	for (const id of query.userIds ?? []) params.append('user_ids', String(id));
	if (query.excludeMeetingId) params.set('exclude_meeting_id', String(query.excludeMeetingId));

	const res = await fetch(`/api/availability?${params}`);
	if (!res.ok) throw new Error(await errorMessage(res, 'Ketersediaan tidak dapat diperiksa.'));
	return res.json();
}
