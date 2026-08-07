import { useCallback, useEffect, useRef, useState } from 'react';
import { useEditor, EditorContent } from '@tiptap/react';
import StarterKit from '@tiptap/starter-kit';
import Placeholder from '@tiptap/extension-placeholder';
import CharacterCount from '@tiptap/extension-character-count';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { chaptersApi, Chapter } from '../lib/api';
import { useEditorStore, useAppStore, useAIStore } from '../stores/appStore';

// ─── Floating Toolbar ─────────────────────────────────────────────────────────

function FloatingToolbar({
  editor,
  onAiAction,
}: {
  editor: ReturnType<typeof useEditor>;
  onAiAction: (mode: string) => void;
}) {
  if (!editor || editor.isEmpty) return null;

  return (
    <div className="floating-toolbar">
      <button
        onClick={() => editor.chain().focus().toggleBold().run()}
        className={editor.isActive('bold') ? 'active' : ''}
        title="Bold (⌘B)"
      >
        B
      </button>
      <button
        onClick={() => editor.chain().focus().toggleItalic().run()}
        className={editor.isActive('italic') ? 'active' : ''}
        title="Italic (⌘I)"
      >
        I
      </button>
      <div className="toolbar-sep" />
      <button
        onClick={() => onAiAction('feedback')}
        title="Get Feedback"
      >
        🔍 Feedback
      </button>
      <button
        onClick={() => onAiAction('copyedit')}
        title="Copyedit"
      >
        ✏️ Copyedit
      </button>
      <button
        onClick={() => onAiAction('revision')}
        title="Revision Pass"
      >
        🔄 Revision
      </button>
    </div>
  );
}

// ─── Save Indicator ───────────────────────────────────────────────────────────

function SaveIndicator() {
  const { isDirty, isSaving } = useEditorStore();

  if (isSaving) return <span className="save-indicator saving">◐ Saving…</span>;
  if (isDirty) return <span className="save-indicator dirty">● Unsaved</span>;
  return <span className="save-indicator saved">● Saved</span>;
}

// ─── Word Count Bar ──────────────────────────────────────────────────────────

function WordCountBar({ chapterWordCount, projectWordCount }: { chapterWordCount: number; projectWordCount: number }) {
  const sessionStartRef = useRef<number>(0);

  useEffect(() => {
    sessionStartRef.current = sessionStartRef.current || chapterWordCount;
  }, []);

  const delta = chapterWordCount - sessionStartRef.current;
  return (
    <div className="word-count-bar">
      <span>Chapter: {chapterWordCount.toLocaleString()} words</span>
      <span>·</span>
      <span>Project: {projectWordCount.toLocaleString()} words</span>
      <span>·</span>
      <span>Session: {delta >= 0 ? '+' : ''}{delta.toLocaleString()}</span>
      <span>·</span>
      <SaveIndicator />
    </div>
  );
}

// ─── Chapter Editor ───────────────────────────────────────────────────────────

export function ChapterEditor({
  chapter,
  projectId,
  onAiAction,
}: {
  chapter: Chapter;
  projectId: string;
  onAiAction: (mode: string) => void;
}) {
  const qc = useQueryClient();
  const addToast = useAppStore((s) => s.addToast);
  const { setContent, setSaving, markSaved, wordCount } = useEditorStore();
  const [title, setTitle] = useState(chapter.title);
  const saveTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  const editor = useEditor({
    extensions: [
      StarterKit,
      Placeholder.configure({ placeholder: 'Begin writing…' }),
      CharacterCount,
    ],
    content: chapter.content,
    onUpdate: ({ editor }) => {
      const html = editor.getHTML();
      setContent(html);
      scheduleAutoSave(html);
    },
  });

  const saveMutation = useMutation({
    mutationFn: (data: { content?: string; title?: string }) =>
      chaptersApi.update(chapter.id, data),
    onSuccess: () => {
      markSaved();
      qc.invalidateQueries({ queryKey: ['chapters', projectId] });
    },
    onError: () => {
      addToast({ type: 'error', message: 'Save failed — retrying…' });
    },
  });

  const scheduleAutoSave = useCallback(
    (content: string) => {
      setSaving(true);
      if (saveTimer.current) clearTimeout(saveTimer.current);
      saveTimer.current = setTimeout(() => {
        saveMutation.mutate({ content });
      }, 2000);
    },
    [saveMutation, setSaving],
  );

  const handleTitleBlur = () => {
    if (title !== chapter.title) {
      saveMutation.mutate({ title });
    }
  };

  // Save on Ctrl/Cmd+S
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 's') {
        e.preventDefault();
        if (saveTimer.current) clearTimeout(saveTimer.current);
        const html = editor?.getHTML() ?? '';
        saveMutation.mutate({ content: html });
      }
    };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [editor, saveMutation]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (saveTimer.current) clearTimeout(saveTimer.current);
    };
  }, []);

  const handleAiAction = (mode: string) => {
    const selectedText = editor?.state.doc.textBetween(
      editor.state.selection.from,
      editor.state.selection.to,
      ' ',
    );
    if (selectedText && selectedText.length > 10) {
      useAIStore.getState().setSelectedPassage(selectedText);
    } else {
      useAIStore.getState().setSelectedPassage('');
    }
    onAiAction(mode);
  };

  return (
    <div className="chapter-editor">
      <div className="chapter-editor__header">
        <input
          className="chapter-title-input"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          onBlur={handleTitleBlur}
          placeholder="Chapter title"
        />
      </div>

      <div className="chapter-editor__canvas">
        {editor && (
          <FloatingToolbar editor={editor} onAiAction={handleAiAction} />
        )}
        <EditorContent editor={editor} className="tiptap-editor" />
      </div>

      <WordCountBar chapterWordCount={wordCount} projectWordCount={0} />
    </div>
  );
}
