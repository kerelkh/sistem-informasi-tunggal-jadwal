<script lang="ts">
	import { untrack } from 'svelte';
	import { createEditor, EditorContent, BubbleMenu } from 'svelte-tiptap';
	import StarterKit from '@tiptap/starter-kit';
	import Placeholder from '@tiptap/extension-placeholder';
	import Image from '@tiptap/extension-image';
	import { HugeiconsIcon } from '@hugeicons/svelte';
	import {
		TextBoldIcon,
		TextItalicIcon,
		TextStrikethroughIcon,
		SourceCodeIcon,
		Link01Icon,
		Heading01Icon,
		Heading02Icon
	} from '@hugeicons/core-free-icons';
	import { SlashCommand } from './slash-command.svelte.js';
	import { EMPTY_DOC } from './empty-doc.js';

	let {
		initialContent,
		onUpdate,
		placeholder = "Tulis sesuatu, atau ketik '/' untuk perintah..."
	}: {
		initialContent?: Record<string, unknown>;
		onUpdate?: (json: object) => void;
		placeholder?: string;
	} = $props();

	// Tiptap owns the document after creation — these only need the value at mount time.
	const startingContent = untrack(() =>
		initialContent && 'type' in initialContent ? initialContent : EMPTY_DOC
	);

	const editor = createEditor({
		extensions: [
			StarterKit.configure({ link: { openOnClick: false, autolink: true } }),
			Placeholder.configure({ placeholder: untrack(() => placeholder) }),
			Image,
			SlashCommand
		],
		content: startingContent,
		editorProps: {
			attributes: {
				class:
					'prose prose-sm sm:prose-base dark:prose-invert max-w-none focus:outline-none min-h-[60vh]'
			}
		},
		onUpdate: ({ editor }) => {
			onUpdate?.(editor.getJSON());
		}
	});

	function setLink() {
		if (!$editor) return;
		const previousUrl = $editor.getAttributes('link').href as string | undefined;
		const url = window.prompt('URL', previousUrl ?? '');
		if (url === null) return;
		if (url === '') {
			$editor.chain().focus().extendMarkRange('link').unsetLink().run();
			return;
		}
		$editor.chain().focus().extendMarkRange('link').setLink({ href: url }).run();
	}
</script>

{#if $editor}
	<BubbleMenu editor={$editor} options={{ placement: 'top', offset: 8 }}>
		<div class="flex items-center gap-0.5 rounded-xl border border-border bg-popover p-1 shadow-md">
			<button
				type="button"
				class="flex size-7 items-center justify-center rounded-lg {$editor.isActive('heading', { level: 1 })
					? 'bg-accent text-accent-foreground'
					: 'hover:bg-muted'}"
				onclick={() => $editor.chain().focus().toggleHeading({ level: 1 }).run()}
			>
				<HugeiconsIcon icon={Heading01Icon} strokeWidth={2} class="size-4" />
			</button>
			<button
				type="button"
				class="flex size-7 items-center justify-center rounded-lg {$editor.isActive('heading', { level: 2 })
					? 'bg-accent text-accent-foreground'
					: 'hover:bg-muted'}"
				onclick={() => $editor.chain().focus().toggleHeading({ level: 2 }).run()}
			>
				<HugeiconsIcon icon={Heading02Icon} strokeWidth={2} class="size-4" />
			</button>
			<div class="mx-0.5 h-4 w-px bg-border"></div>
			<button
				type="button"
				class="flex size-7 items-center justify-center rounded-lg {$editor.isActive('bold')
					? 'bg-accent text-accent-foreground'
					: 'hover:bg-muted'}"
				onclick={() => $editor.chain().focus().toggleBold().run()}
			>
				<HugeiconsIcon icon={TextBoldIcon} strokeWidth={2} class="size-4" />
			</button>
			<button
				type="button"
				class="flex size-7 items-center justify-center rounded-lg {$editor.isActive('italic')
					? 'bg-accent text-accent-foreground'
					: 'hover:bg-muted'}"
				onclick={() => $editor.chain().focus().toggleItalic().run()}
			>
				<HugeiconsIcon icon={TextItalicIcon} strokeWidth={2} class="size-4" />
			</button>
			<button
				type="button"
				class="flex size-7 items-center justify-center rounded-lg {$editor.isActive('strike')
					? 'bg-accent text-accent-foreground'
					: 'hover:bg-muted'}"
				onclick={() => $editor.chain().focus().toggleStrike().run()}
			>
				<HugeiconsIcon icon={TextStrikethroughIcon} strokeWidth={2} class="size-4" />
			</button>
			<button
				type="button"
				class="flex size-7 items-center justify-center rounded-lg {$editor.isActive('code')
					? 'bg-accent text-accent-foreground'
					: 'hover:bg-muted'}"
				onclick={() => $editor.chain().focus().toggleCode().run()}
			>
				<HugeiconsIcon icon={SourceCodeIcon} strokeWidth={2} class="size-4" />
			</button>
			<button
				type="button"
				class="flex size-7 items-center justify-center rounded-lg {$editor.isActive('link')
					? 'bg-accent text-accent-foreground'
					: 'hover:bg-muted'}"
				onclick={setLink}
			>
				<HugeiconsIcon icon={Link01Icon} strokeWidth={2} class="size-4" />
			</button>
		</div>
	</BubbleMenu>
{/if}

<EditorContent editor={$editor} />
