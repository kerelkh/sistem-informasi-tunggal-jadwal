export type UserRole = 'admin' | 'user';

export interface UnitSummary {
	id: number;
	name: string;
}

export interface CurrentUser {
	id: number;
	email: string;
	full_name: string | null;
	position: string | null;
	role: UserRole;
	unit: UnitSummary | null;
	is_active: boolean;
	created_at: string;
}

/** Any account, as the admin Users screen sees it. */
export type UserRecord = CurrentUser;

export interface Unit {
	id: number;
	name: string;
	code: string | null;
	description: string | null;
	member_count: number;
	created_at: string;
}

/** Just enough about a person to show who they are. */
export interface UserBrief {
	id: number;
	full_name: string | null;
	email: string;
	position: string | null;
	unit_name: string | null;
}

export function displayName(user: { full_name: string | null; email: string }): string {
	return user.full_name || user.email.split('@')[0];
}

export function initials(user: { full_name: string | null; email: string }): string {
	const words = displayName(user).trim().split(/\s+/);
	return (words.length > 1 ? words[0][0] + words[1][0] : words[0].slice(0, 2)).toUpperCase();
}
