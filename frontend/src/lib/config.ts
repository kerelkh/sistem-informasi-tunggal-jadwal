import { env } from '$env/dynamic/public';

/** Branding — override via PUBLIC_APP_NAME / PUBLIC_APP_TAGLINE in .env. */
export const APP_NAME = env.PUBLIC_APP_NAME || 'SITUNG';
export const APP_TAGLINE = env.PUBLIC_APP_TAGLINE || 'Sistem Informasi Tunggal Jadwal';

