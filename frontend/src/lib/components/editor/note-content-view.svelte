<script lang="ts">
	import { untrack } from 'svelte';
	import { createEditor, EditorContent } from 'svelte-tiptap';
	import StarterKit from '@tiptap/starter-kit';
	import Image from '@tiptap/extension-image';
	import { EMPTY_DOC } from './empty-doc.js';
	import { assignHeadingIds } from '$lib/utils/headings.js';

	let { content }: { content: Record<string, unknown> } = $props();

	// Tiptap owns the document after creation — this only needs the value at mount time.
	const startingContent = untrack(() => (content && 'type' in content ? content : EMPTY_DOC));

	const editor = createEditor({
		extensions: [StarterKit.configure({ link: { openOnClick: true } }), Image],
		content: startingContent,
		editable: false,
		editorProps: {
			attributes: {
				class: 'prose prose-sm sm:prose-base dark:prose-invert max-w-none focus:outline-none'
			}
		},
		onCreate: ({ editor }) => {
			assignHeadingIds(editor.view.dom as HTMLElement);
		}
	});
</script>

<EditorContent editor={$editor} />
