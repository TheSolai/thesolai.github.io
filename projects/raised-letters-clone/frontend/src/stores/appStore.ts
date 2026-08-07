import { create } from 'zustand';

// ─── Toast ───────────────────────────────────────────────────────────────────

export interface Toast {
  id: string;
  type: 'success' | 'error' | 'info';
  message: string;
}

// ─── App Store ───────────────────────────────────────────────────────────────

interface AppState {
  currentProjectId: string | null;
  currentChapterId: string | null;
  aiPanelOpen: boolean;
  sidebarSection: 'chapters' | 'companions' | 'checkpoints';
  toasts: Toast[];

  setCurrentProject: (id: string | null) => void;
  setCurrentChapter: (id: string | null) => void;
  toggleAiPanel: () => void;
  setSidebarSection: (s: 'chapters' | 'companions' | 'checkpoints') => void;
  addToast: (t: Omit<Toast, 'id'>) => void;
  removeToast: (id: string) => void;
}

export const useAppStore = create<AppState>((set) => ({
  currentProjectId: null,
  currentChapterId: null,
  aiPanelOpen: false,
  sidebarSection: 'chapters',
  toasts: [],

  setCurrentProject: (id) => set({ currentProjectId: id, currentChapterId: null }),
  setCurrentChapter: (id) => set({ currentChapterId: id }),
  toggleAiPanel: () => set((s) => ({ aiPanelOpen: !s.aiPanelOpen })),
  setSidebarSection: (s) => set({ sidebarSection: s }),
  addToast: (t) => set((s) => ({ toasts: [...s.toasts, { ...t, id: Date.now().toString() }] })),
  removeToast: (id) => set((s) => ({ toasts: s.toasts.filter((t) => t.id !== id) })),
}));

// ─── Editor Store ─────────────────────────────────────────────────────────────

interface EditorState {
  content: string;
  isDirty: boolean;
  isSaving: boolean;
  lastSaved: Date | null;
  wordCount: number;

  setContent: (c: string) => void;
  setSaving: (v: boolean) => void;
  markSaved: () => void;
  computeWordCount: (text: string) => void;
}

function countWords(text: string): number {
  return text.trim().split(/\s+/).filter(Boolean).length;
}

export const useEditorStore = create<EditorState>((set) => ({
  content: '',
  isDirty: false,
  isSaving: false,
  lastSaved: null,
  wordCount: 0,

  setContent: (content) => set({ content, isDirty: true, wordCount: countWords(content) }),
  setSaving: (isSaving) => set({ isSaving }),
  markSaved: () => set({ isDirty: false, isSaving: false, lastSaved: new Date() }),
  computeWordCount: (text) => set({ wordCount: countWords(text) }),
}));

// ─── AI Store ─────────────────────────────────────────────────────────────────

type AIMode = 'feedback' | 'copyedit' | 'format' | 'revision';

interface AIState {
  selectedPersonaId: string;
  activeMode: AIMode;
  isLoading: boolean;
  response: string;
  annotations: Array<{
    start: number;
    end: number;
    type: string;
    message: string;
    suggestion?: string;
    dismissed?: boolean;
  }>;
  selectedPassage: string;

  setPersona: (id: string) => void;
  setMode: (m: AIMode) => void;
  setLoading: (v: boolean) => void;
  setResponse: (r: string) => void;
  setAnnotations: (a: AIState['annotations']) => void;
  dismissAnnotation: (i: number) => void;
  setSelectedPassage: (s: string) => void;
  reset: () => void;
}

export const useAIStore = create<AIState>((set) => ({
  selectedPersonaId: '',
  activeMode: 'feedback',
  isLoading: false,
  response: '',
  annotations: [],
  selectedPassage: '',

  setPersona: (id) => set({ selectedPersonaId: id }),
  setMode: (mode) => set({ activeMode: mode, response: '', annotations: [] }),
  setLoading: (isLoading) => set({ isLoading }),
  setResponse: (response) => set({ response }),
  setAnnotations: (annotations) => set({ annotations }),
  dismissAnnotation: (i) =>
    set((s) => ({
      annotations: s.annotations.map((a, idx) => (idx === i ? { ...a, dismissed: true } : a)),
    })),
  setSelectedPassage: (selectedPassage) => set({ selectedPassage }),
  reset: () => set({ response: '', annotations: [], isLoading: false }),
}));
