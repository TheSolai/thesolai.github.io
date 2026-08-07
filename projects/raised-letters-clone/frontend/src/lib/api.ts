import axios from 'axios';

const API = axios.create({
  baseURL: 'http://localhost:8000/api',
  timeout: 120_000,
});

export default API;

// ─── Types ───────────────────────────────────────────────────────────────────

export interface Project {
  id: string;
  title: string;
  subtitle: string;
  author: string;
  genre: string;
  created_at: string;
  updated_at: string;
  word_count?: number;
  chapter_count?: number;
}

export interface Chapter {
  id: string;
  project_id: string;
  title: string;
  order_index: number;
  content: string;
  word_count: number;
  created_at: string;
  updated_at: string;
}

export interface Checkpoint {
  id: string;
  chapter_id: string;
  name: string;
  content: string;
  word_count: number;
  created_at: string;
}

export interface Companion {
  id: string;
  project_id: string;
  type: 'world_bible' | 'style_guide' | 'editorial_letter';
  content: string | Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

export interface Character {
  id: string;
  companion_id: string;
  name: string;
  role: string;
  description: string;
  first_appearance: string;
  details: string;
  created_at: string;
  updated_at: string;
}

export interface Persona {
  id: string;
  name: string;
  description: string;
  system_prompt: string;
  is_active: boolean;
}

export interface Annotation {
  start: number;
  end: number;
  type: string;
  message: string;
  suggestion?: string;
}

export interface AISettings {
  ai_model: string;
  ai_engine: string;
  ai_temperature: number;
  ai_max_tokens: number;
}

export interface AIResponse {
  annotations: Annotation[];
  summary: string;
  tokens_used?: number;
  model?: string;
}

export interface WordCountHistory {
  date: string;
  words_written: number;
}

// ─── Projects ────────────────────────────────────────────────────────────────

export const projectsApi = {
  list: () => API.get<Project[]>('/projects').then(r => r.data),
  get: (id: string) => API.get<Project>(`/projects/${id}`).then(r => r.data),
  create: (data: Partial<Project>) => API.post<Project>('/projects', data).then(r => r.data),
  update: (id: string, data: Partial<Project>) => API.patch<Project>(`/projects/${id}`, data).then(r => r.data),
  delete: (id: string) => API.delete(`/projects/${id}`),
  wordCountHistory: (id: string) => API.get<WordCountHistory[]>(`/projects/${id}/word-count-history`).then(r => r.data),
};

// ─── Chapters ────────────────────────────────────────────────────────────────

export const chaptersApi = {
  listForProject: (pid: string) => API.get<Chapter[]>(`/chapters/for-project/${pid}`).then(r => r.data),
  get: (id: string) => API.get<Chapter>(`/chapters/${id}`).then(r => r.data),
  create: (pid: string, data: Partial<Chapter>) => API.post<Chapter>('/chapters', { ...data, project_id: pid }).then(r => r.data),
  update: (id: string, data: Partial<Chapter>) => API.patch<Chapter>(`/chapters/${id}`, data).then(r => r.data),
  delete: (id: string) => API.delete(`/chapters/${id}`),
  reorder: (pid: string, orderedIds: string[]) => API.post(`/chapters/reorder/${pid}`, { ordered_ids: orderedIds }),
};

// ─── Checkpoints ─────────────────────────────────────────────────────────────

export const checkpointsApi = {
  listForChapter: (cid: string) => API.get<Checkpoint[]>(`/checkpoints/for-chapter/${cid}`).then(r => r.data),
  get: (id: string) => API.get<Checkpoint>(`/checkpoints/${id}`).then(r => r.data),
  create: (cid: string, name: string) => API.post<Checkpoint>('/checkpoints', { chapter_id: cid, name }).then(r => r.data),
  delete: (id: string) => API.delete(`/checkpoints/${id}`),
  restore: (cid: string, cpid: string) => API.post<Chapter>(`/chapters/${cid}/restore/${cpid}`).then(r => r.data),
};

// ─── Companions ─────────────────────────────────────────────────────────────

export const companionsApi = {
  listForProject: (pid: string) => API.get<Companion[]>(`/companions/for-project/${pid}`).then(r => r.data),
  upsert: (pid: string, type: Companion['type'], content: string | Record<string, unknown>) =>
    API.post<Companion>('/companions', { project_id: pid, type, content }).then(r => r.data),
  delete: (id: string) => API.delete(`/companions/${id}`),
  listCharacters: (cid: string) => API.get<Character[]>(`/companions/${cid}/characters`).then(r => r.data),
  createCharacter: (cid: string, data: Partial<Character>) =>
    API.post<Character>(`/companions/${cid}/characters`, data).then(r => r.data),
  updateCharacter: (id: string, data: Partial<Character>) =>
    API.patch<Character>(`/companions/characters/${id}`, data).then(r => r.data),
  deleteCharacter: (id: string) => API.delete(`/companions/characters/${id}`),
};

// ─── AI ──────────────────────────────────────────────────────────────────────

export const aiApi = {
  status: () => API.get<{ status: string; models?: string[]; error?: string }>('/ai/status').then(r => r.data),
  settings: () => API.get<AISettings>('/ai/settings').then(r => r.data),
  updateSettings: (data: Partial<AISettings>) => API.patch<AISettings>('/ai/settings', data).then(r => r.data),
  personas: () => API.get<Persona[]>('/ai/personas').then(r => r.data),
  persona: (id: string) => API.get<Persona>(`/ai/personas/${id}`).then(r => r.data),
  feedback: (data: { project_id: string; chapter_id: string; passage: string; persona_id?: string }) =>
    API.post<AIResponse>('/ai/feedback', data).then(r => r.data),
  copyedit: (data: { project_id: string; chapter_id: string; passage: string; persona_id?: string }) =>
    API.post<AIResponse>('/ai/copyedit', data).then(r => r.data),
  formatCheck: (data: { project_id: string; chapter_id: string; passage: string }) =>
    API.post<AIResponse>('/ai/format-check', data).then(r => r.data),
  revisionPass: (data: { project_id: string; chapter_id: string; passage: string; persona_id?: string }) =>
    API.post<AIResponse>('/ai/revision-pass', data).then(r => r.data),
};
