import {
	Building03Icon,
	Calendar03Icon,
	CalendarCheckIn01Icon,
	DashboardSquare01Icon,
	MailReceive01Icon,
	Settings02Icon,
	Task01Icon,
	UserMultiple02Icon
} from '@hugeicons/core-free-icons';
import type { IconSvgElement } from '@hugeicons/svelte';
import type { UserRole } from '$lib/types/user';

export type NavItem = { title: string; url: string; icon?: IconSvgElement; badge?: number };
export type NavGroup = { label?: string; items: NavItem[] };

const MEMBER_NAV: NavGroup[] = [
	{
		items: [{ title: 'Beranda', url: '/dashboard', icon: DashboardSquare01Icon }]
	},
	{
		label: 'Jadwal',
		items: [
			{ title: 'Kalender', url: '/dashboard/calendar', icon: Calendar03Icon },
			{ title: 'Rapat Saya', url: '/dashboard/meetings', icon: Task01Icon },
			{ title: 'Undangan', url: '/dashboard/invitations', icon: MailReceive01Icon },
			{ title: 'Ketersediaan', url: '/dashboard/availability', icon: CalendarCheckIn01Icon }
		]
	}
];

const ADMIN_NAV: NavGroup = {
	label: 'Administrasi',
	items: [
		{ title: 'Unit Kerja', url: '/dashboard/admin/units', icon: Building03Icon },
		{ title: 'Pengguna', url: '/dashboard/admin/users', icon: UserMultiple02Icon }
	]
};

const ACCOUNT_NAV: NavGroup = {
	label: 'Akun',
	items: [
		{ title: 'Pengaturan', url: '/dashboard/settings', icon: Settings02Icon }
	]
};

/**
 * The dashboard's navigation. Administration only appears for admins — the backend
 * refuses those calls for anyone else anyway, this just keeps dead ends out of sight.
 */
export function dashboardNav(role: UserRole, pendingInvitations: number): NavGroup[] {
	const groups = [...MEMBER_NAV, ...(role === 'admin' ? [ADMIN_NAV] : []), ACCOUNT_NAV];
	return groups.map((group) => ({
		...group,
		items: group.items.map((item) =>
			item.url === '/dashboard/invitations' ? { ...item, badge: pendingInvitations } : item
		)
	}));
}

/**
 * Overview matches only its exact path — every dashboard URL starts with /dashboard,
 * so a prefix test would light it up everywhere. The rest match by prefix so that
 * nested pages (a meeting's detail or edit view) still highlight their section.
 */
export function isNavItemActive(url: string, pathname: string): boolean {
	if (url === '/dashboard') return pathname === '/dashboard';
	return pathname === url || pathname.startsWith(`${url}/`);
}
