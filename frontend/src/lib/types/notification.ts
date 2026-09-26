export type NotificationType =
	| 'meeting_invitation'
	| 'invitation_revoked'
	| 'meeting_updated'
	| 'meeting_cancelled'
	| 'invitation_accepted'
	| 'invitation_declined'
	| 'invitation_cancelled';

export interface Notification {
	id: number;
	type: NotificationType;
	title: string;
	body: string | null;
	link: string | null;
	/** The moment the notification is about, e.g. the meeting's start. */
	event_at: string | null;
	is_read: boolean;
	created_at: string;
}
