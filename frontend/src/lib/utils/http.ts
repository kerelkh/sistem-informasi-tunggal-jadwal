/** Reads a FastAPI error body into one sentence for the UI. */
export async function errorMessage(
	res: Response,
	fallback = 'Terjadi kesalahan. Silakan coba lagi.'
): Promise<string> {
	const data = await res.json().catch(() => null);
	if (typeof data?.detail === 'string') return data.detail;
	if (Array.isArray(data?.detail) && data.detail[0]?.msg) return String(data.detail[0].msg);
	return fallback;
}
