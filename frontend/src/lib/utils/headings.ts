export interface Heading {
	id: string;
	text: string;
	level: number;
}

export function slugify(text: string): string {
	return text.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/(^-|-$)/g, '') || 'section';
}

function dedupe(slug: string, seen: Map<string, number>): string {
	const count = seen.get(slug) ?? 0;
	seen.set(slug, count + 1);
	return count > 0 ? `${slug}-${count}` : slug;
}

/** Walks a Tiptap JSON document and extracts headings for a table of contents. */
export function extractHeadings(content: unknown): Heading[] {
	const headings: Heading[] = [];
	const seen = new Map<string, number>();

	function walk(node: unknown) {
		if (!node || typeof node !== 'object') return;
		const n = node as { type?: string; attrs?: { level?: number }; content?: unknown[] };

		if (n.type === 'heading') {
			const text = (n.content ?? [])
				.map((child) => (child as { text?: string }).text ?? '')
				.join('');
			if (text) {
				headings.push({ id: dedupe(slugify(text), seen), text, level: n.attrs?.level ?? 1 });
			}
		}

		n.content?.forEach(walk);
	}

	walk(content);
	return headings;
}

/** Walks a Tiptap JSON document and returns its plain text, truncated to maxLength. */
export function extractText(content: unknown, maxLength = 200): string {
	const parts: string[] = [];

	function walk(node: unknown) {
		if (!node || typeof node !== 'object') return;
		const n = node as { text?: string; content?: unknown[] };
		if (n.text) parts.push(n.text);
		n.content?.forEach(walk);
	}

	walk(content);
	const text = parts.join(' ').replace(/\s+/g, ' ').trim();
	return text.length > maxLength ? `${text.slice(0, maxLength).trimEnd()}…` : text;
}

/** Assigns ids to rendered heading elements, matching extractHeadings' slug/dedupe logic. */
export function assignHeadingIds(root: HTMLElement) {
	const seen = new Map<string, number>();
	root.querySelectorAll('h1, h2, h3').forEach((el) => {
		const heading = el as HTMLElement;
		heading.id = dedupe(slugify(heading.textContent ?? ''), seen);
		heading.style.scrollMarginTop = '5rem';
	});
}
