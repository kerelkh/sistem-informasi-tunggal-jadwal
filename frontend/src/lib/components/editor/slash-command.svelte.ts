import {
	Heading01Icon,
	Heading02Icon,
	Heading03Icon,
	LeftToRightListBulletIcon,
	LeftToRightListNumberIcon,
	QuoteDownIcon,
	SourceCodeIcon,
	MinusSignIcon,
	Image01Icon
} from '@hugeicons/core-free-icons';
import { Extension } from '@tiptap/core';
import Suggestion, { type SuggestionOptions } from '@tiptap/suggestion';
import { computePosition, flip, shift, offset } from '@floating-ui/dom';
import { mount, unmount } from 'svelte';
import SlashCommandList, { type SlashCommandItem } from './slash-command-list.svelte';


const allCommands: SlashCommandItem[] = [
	{
		title: 'Judul 1',
		icon: Heading01Icon,
		command: ({ editor, range }) => editor.chain().focus().deleteRange(range).setNode('heading', { level: 1 }).run()
	},
	{
		title: 'Judul 2',
		icon: Heading02Icon,
		command: ({ editor, range }) => editor.chain().focus().deleteRange(range).setNode('heading', { level: 2 }).run()
	},
	{
		title: 'Judul 3',
		icon: Heading03Icon,
		command: ({ editor, range }) => editor.chain().focus().deleteRange(range).setNode('heading', { level: 3 }).run()
	},
	{
		title: 'Daftar poin',
		icon: LeftToRightListBulletIcon,
		command: ({ editor, range }) => editor.chain().focus().deleteRange(range).toggleBulletList().run()
	},
	{
		title: 'Daftar bernomor',
		icon: LeftToRightListNumberIcon,
		command: ({ editor, range }) => editor.chain().focus().deleteRange(range).toggleOrderedList().run()
	},
	{
		title: 'Kutipan',
		icon: QuoteDownIcon,
		command: ({ editor, range }) => editor.chain().focus().deleteRange(range).toggleBlockquote().run()
	},
	{
		title: 'Blok kode',
		icon: SourceCodeIcon,
		command: ({ editor, range }) => editor.chain().focus().deleteRange(range).toggleCodeBlock().run()
	},
	{
		title: 'Garis pemisah',
		icon: MinusSignIcon,
		command: ({ editor, range }) => editor.chain().focus().deleteRange(range).setHorizontalRule().run()
	},
	{
		title: 'Gambar',
		icon: Image01Icon,
		command: ({ editor, range }) => {
			const url = window.prompt('URL gambar');
			if (!url) return;
			editor.chain().focus().deleteRange(range).setImage({ src: url }).run();
		}
	}
];

const suggestion: Omit<SuggestionOptions<SlashCommandItem>, 'editor'> = {
	char: '/',
	items: ({ query }) =>
		allCommands.filter((item) => item.title.toLowerCase().includes(query.toLowerCase())),

	command: ({ editor, range, props }) => {
		props.command({ editor, range });
	},

	render: () => {
		let mountHandle: Record<string, unknown> | undefined;
		let element: HTMLDivElement;
		let itemsState = $state<SlashCommandItem[]>([]);
		let selectedIndex = $state(0);
		let selectItem: ((item: SlashCommandItem) => void) | undefined;

		function updatePosition(clientRect: (() => DOMRect | null) | null | undefined) {
			const rect = clientRect?.();
			if (!rect) return;
			const virtualEl = {
				getBoundingClientRect: () => rect
			};
			computePosition(virtualEl, element, {
				placement: 'bottom-start',
				middleware: [offset(6), flip(), shift({ padding: 8 })]
			}).then(({ x, y }) => {
				Object.assign(element.style, { left: `${x}px`, top: `${y}px` });
			});
		}

		return {
			onStart: (props) => {
				itemsState = props.items;
				selectedIndex = 0;
				selectItem = (item) => props.command(item);

				element = document.createElement('div');
				element.style.position = 'absolute';
				element.style.zIndex = '50';
				// Prevent the editor from losing its selection (and thus exiting the
				// suggestion) when clicking inside the popup, which lives outside the
				// editor's own DOM since it's appended directly to <body>.
				element.addEventListener('mousedown', (event) => event.preventDefault());
				document.body.appendChild(element);

				mountHandle = mount(SlashCommandList, {
					target: element,
					props: {
						get items() {
							return itemsState;
						},
						get selectedIndex() {
							return selectedIndex;
						},
						command: (item: SlashCommandItem) => selectItem?.(item)
					}
				}) as unknown as Record<string, unknown>;

				updatePosition(props.clientRect);
			},

			onUpdate: (props) => {
				itemsState = props.items;
				selectedIndex = 0;
				selectItem = (item) => props.command(item);
				updatePosition(props.clientRect);
			},

			onKeyDown: (props) => {
				const { event } = props;

				if (event.key === 'Escape') {
					element?.remove();
					return true;
				}

				if (event.key === 'ArrowUp') {
					selectedIndex = (selectedIndex + itemsState.length - 1) % itemsState.length;
					return true;
				}

				if (event.key === 'ArrowDown') {
					selectedIndex = (selectedIndex + 1) % itemsState.length;
					return true;
				}

				if (event.key === 'Enter') {
					const item = itemsState[selectedIndex];
					if (item) selectItem?.(item);
					return true;
				}

				return false;
			},

			onExit: () => {
				if (mountHandle) unmount(mountHandle as Parameters<typeof unmount>[0]);
				element?.remove();
			}
		};
	}
};

export const SlashCommand = Extension.create({
	name: 'slashCommand',

	addOptions() {
		return { suggestion };
	},

	addProseMirrorPlugins() {
		return [
			Suggestion({
				editor: this.editor,
				...this.options.suggestion
			})
		];
	}
});
