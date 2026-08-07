import { useState, useEffect, useRef } from 'react';
import { useParams } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { companionsApi, Character } from '../lib/api';
import { useAppStore } from '../stores/appStore';

// ─── World Bible — Character Form ─────────────────────────────────────────────

interface CharacterFormState {
  id?: string;
  name: string;
  role: string;
  description: string;
  first_appearance: string;
}

function CharacterForm({
  initial,
  companionId,
  onSave,
  onCancel,
}: {
  initial?: Character;
  companionId: string;
  onSave: () => void;
  onCancel: () => void;
}) {
  const qc = useQueryClient();
  const addToast = useAppStore((s) => s.addToast);
  const [form, setForm] = useState<CharacterFormState>({
    id: initial?.id,
    name: initial?.name || '',
    role: initial?.role || '',
    description: initial?.description || '',
    first_appearance: initial?.first_appearance || '',
  });

  const createMutation = useMutation({
    mutationFn: (data: Partial<Character>) =>
      companionsApi.createCharacter(companionId, data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['characters', companionId] });
      addToast({ type: 'success', message: 'Character added.' });
      onSave();
    },
    onError: () => addToast({ type: 'error', message: 'Failed to add character.' }),
  });

  const updateMutation = useMutation({
    mutationFn: (data: Partial<Character>) =>
      companionsApi.updateCharacter(initial!.id, data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['characters', companionId] });
      addToast({ type: 'success', message: 'Character updated.' });
      onSave();
    },
    onError: () => addToast({ type: 'error', message: 'Failed to update character.' }),
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.name.trim()) return;
    const payload = { name: form.name, role: form.role, description: form.description, first_appearance: form.first_appearance };
    if (initial?.id) {
      updateMutation.mutate(payload);
    } else {
      createMutation.mutate(payload);
    }
  };

  return (
    <form className="character-form" onSubmit={handleSubmit}>
      <label className="form-field">
        Name <span className="required">*</span>
        <input
          autoFocus
          type="text"
          value={form.name}
          onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))}
          placeholder="Character name"
          required
        />
      </label>
      <label className="form-field">
        Role
        <input
          type="text"
          value={form.role}
          onChange={(e) => setForm((f) => ({ ...f, role: e.target.value }))}
          placeholder="Protagonist, Antagonist, Supporting…"
        />
      </label>
      <label className="form-field">
        First Appearance
        <input
          type="text"
          value={form.first_appearance}
          onChange={(e) => setForm((f) => ({ ...f, first_appearance: e.target.value }))}
          placeholder="Chapter reference"
        />
      </label>
      <label className="form-field">
        Description
        <textarea
          value={form.description}
          onChange={(e) => setForm((f) => ({ ...f, description: e.target.value }))}
          placeholder="Character description…"
          rows={4}
        />
      </label>
      <div className="form-actions">
        <button type="button" className="btn btn--ghost" onClick={onCancel}>Cancel</button>
        <button
          type="submit"
          className="btn btn--primary"
          disabled={createMutation.isPending || updateMutation.isPending}
        >
          {initial ? 'Save Changes' : 'Add Character'}
        </button>
      </div>
    </form>
  );
}

// ─── World Bible Tab ───────────────────────────────────────────────────────────

function WorldBibleTab({ projectId }: { projectId: string }) {
  const qc = useQueryClient();
  const addToast = useAppStore((s) => s.addToast);

  const { data: companions = [] } = useQuery({
    queryKey: ['companions', projectId],
    queryFn: () => companionsApi.listForProject(projectId),
  });

  const wbCompanion = companions.find((c) => c.type === 'world_bible');
  const companionId = wbCompanion?.id || '';

  const { data: characters = [], isLoading } = useQuery({
    queryKey: ['characters', companionId],
    queryFn: () => companionsApi.listCharacters(companionId),
    enabled: !!companionId,
  });

  const upsertWb = useMutation({
    mutationFn: () => companionsApi.upsert(projectId, 'world_bible', ''),
    onSuccess: (data) => {
      qc.invalidateQueries({ queryKey: ['companions', projectId] });
      return data;
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => companionsApi.deleteCharacter(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['characters', companionId] });
      addToast({ type: 'success', message: 'Character deleted.' });
    },
    onError: () => addToast({ type: 'error', message: 'Failed to delete character.' }),
  });

  const [editingId, setEditingId] = useState<string | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [expandedId, setExpandedId] = useState<string | null>(null);

  const editingChar = characters.find((c) => c.id === editingId);

  const handleAdd = async () => {
    if (!wbCompanion) {
      await upsertWb.mutateAsync();
    }
    setShowForm(true);
    setEditingId(null);
  };

  const handleEdit = (id: string) => {
    setEditingId(id);
    setShowForm(true);
  };

  return (
    <div className="companion-tab world-bible-tab">
      {isLoading ? (
        <div className="loading-state">Loading characters…</div>
      ) : characters.length === 0 && !showForm ? (
        <div className="empty-state empty-state--small">
          <p>No characters yet.</p>
          <button className="btn btn--primary btn--small" onClick={handleAdd}>
            + Add Character
          </button>
        </div>
      ) : (
        <div className="character-list">
          {characters.map((char) => (
            <div key={char.id} className="character-card">
              <div
                className="character-card__header"
                onClick={() => setExpandedId(expandedId === char.id ? null : char.id)}
              >
                <div>
                  <strong>{char.name}</strong>
                  {char.role && <span className="character-card__role"> · {char.role}</span>}
                </div>
                <div className="character-card__actions" onClick={(e) => e.stopPropagation()}>
                  <button className="btn btn--ghost btn--small" onClick={() => handleEdit(char.id)}>Edit</button>
                  <button
                    className="btn btn--ghost btn--small btn--danger"
                    onClick={() => deleteMutation.mutate(char.id)}
                  >
                    Delete
                  </button>
                </div>
              </div>
              {expandedId === char.id && char.description && (
                <p className="character-card__description">{char.description}</p>
              )}
            </div>
          ))}
        </div>
      )}

      {showForm && (
        <div className="companion-form-overlay">
          <CharacterForm
            initial={editingChar}
            companionId={companionId}
            onSave={() => { setShowForm(false); setEditingId(null); }}
            onCancel={() => { setShowForm(false); setEditingId(null); }}
          />
        </div>
      )}

      {(characters.length > 0 || showForm) && !showForm && (
        <button className="btn btn--ghost btn--small companion-tab__add" onClick={handleAdd}>
          + Add Character
        </button>
      )}
    </div>
  );
}

// ─── Style Guide Tab ──────────────────────────────────────────────────────────

function StyleGuideTab({ projectId }: { projectId: string }) {
  const qc = useQueryClient();
  const addToast = useAppStore((s) => s.addToast);
  const saveTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  const { data: companions = [] } = useQuery({
    queryKey: ['companions', projectId],
    queryFn: () => companionsApi.listForProject(projectId),
  });

  const sgCompanion = companions.find((c) => c.type === 'style_guide');
  const [content, setContent] = useState(sgCompanion?.content as string || '');

  useEffect(() => {
    if (sgCompanion) {
      setContent(sgCompanion.content as string || '');
    }
  }, [sgCompanion]);

  const upsertMutation = useMutation({
    mutationFn: (val: string) => companionsApi.upsert(projectId, 'style_guide', val),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['companions', projectId] }),
    onError: () => addToast({ type: 'error', message: 'Failed to save style guide.' }),
  });

  const handleBlur = () => {
    if (saveTimer.current) clearTimeout(saveTimer.current);
    saveTimer.current = setTimeout(() => {
      upsertMutation.mutate(content);
    }, 2000);
  };

  return (
    <div className="companion-tab style-guide-tab">
      <textarea
        className="companion-textarea"
        value={content}
        onChange={(e) => setContent(e.target.value)}
        onBlur={handleBlur}
        placeholder="Writing style rules… (auto-saves on blur)"
        rows={12}
      />
    </div>
  );
}

// ─── Editorial Letter Tab ─────────────────────────────────────────────────────

function EditorialLetterTab({ projectId }: { projectId: string }) {
  const qc = useQueryClient();
  const addToast = useAppStore((s) => s.addToast);
  const saveTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  const { data: companions = [] } = useQuery({
    queryKey: ['companions', projectId],
    queryFn: () => companionsApi.listForProject(projectId),
  });

  const elCompanion = companions.find((c) => c.type === 'editorial_letter');
  const [content, setContent] = useState(elCompanion?.content as string || '');

  useEffect(() => {
    if (elCompanion) {
      setContent(elCompanion.content as string || '');
    }
  }, [elCompanion]);

  const upsertMutation = useMutation({
    mutationFn: (val: string) => companionsApi.upsert(projectId, 'editorial_letter', val),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['companions', projectId] }),
    onError: () => addToast({ type: 'error', message: 'Failed to save editorial letter.' }),
  });

  const handleBlur = () => {
    if (saveTimer.current) clearTimeout(saveTimer.current);
    saveTimer.current = setTimeout(() => {
      upsertMutation.mutate(content);
    }, 2000);
  };

  return (
    <div className="companion-tab editorial-letter-tab">
      <textarea
        className="companion-textarea"
        value={content}
        onChange={(e) => setContent(e.target.value)}
        onBlur={handleBlur}
        placeholder="Themes to preserve, known problem areas, what you're trying to achieve…"
        rows={12}
      />
    </div>
  );
}

// ─── CompanionDocs ─────────────────────────────────────────────────────────────

export function CompanionDocs() {
  const { projectId } = useParams<{ projectId: string }>();
  const [activeTab, setActiveTab] = useState<'world' | 'style' | 'letter'>('world');

  if (!projectId) return null;

  return (
    <div className="companion-panel">
      <div className="companion-panel__tabs" role="tablist">
        <button
          role="tab"
          aria-selected={activeTab === 'world'}
          className={`companion-panel__tab${activeTab === 'world' ? ' active' : ''}`}
          onClick={() => setActiveTab('world')}
        >
          World Bible
        </button>
        <button
          role="tab"
          aria-selected={activeTab === 'style'}
          className={`companion-panel__tab${activeTab === 'style' ? ' active' : ''}`}
          onClick={() => setActiveTab('style')}
        >
          Style Guide
        </button>
        <button
          role="tab"
          aria-selected={activeTab === 'letter'}
          className={`companion-panel__tab${activeTab === 'letter' ? ' active' : ''}`}
          onClick={() => setActiveTab('letter')}
        >
          Editorial Letter
        </button>
      </div>

      <div className="companion-panel__body">
        {activeTab === 'world' && <WorldBibleTab projectId={projectId} />}
        {activeTab === 'style' && <StyleGuideTab projectId={projectId} />}
        {activeTab === 'letter' && <EditorialLetterTab projectId={projectId} />}
      </div>
    </div>
  );
}
