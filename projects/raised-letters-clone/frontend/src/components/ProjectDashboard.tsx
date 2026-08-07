import React, { useState, useCallback, useEffect } from 'react';
import { useParams, useNavigate, Link, Navigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { projectsApi, chaptersApi, Chapter } from '../lib/api';
import { useAppStore } from '../stores/appStore';
import { ChapterEditor } from './Editor';
import { AIPanel } from './AIPanel';
import { CompanionDocs } from './CompanionDocs';
import { CheckpointPanel } from './CheckpointPanel';
import { ToastContainer } from './Toast';

// ─── New Chapter Modal ────────────────────────────────────────────────────────

function NewChapterModal({ projectId, onClose, onCreated }: { projectId: string; onClose: () => void; onCreated: () => void }) {
  const qc = useQueryClient();
  const addToast = useAppStore((s) => s.addToast);
  const [title, setTitle] = useState('');

  const createMutation = useMutation({
    mutationFn: (data: Partial<Chapter>) => chaptersApi.create(projectId, data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['chapters', projectId] });
      addToast({ type: 'success', message: 'Chapter created.' });
      onCreated();
      onClose();
    },
    onError: () => addToast({ type: 'error', message: 'Failed to create chapter.' }),
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const t = title.trim() || `Chapter ${Date.now()}`;
    createMutation.mutate({ title: t });
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        <div className="modal__header">
          <h2>New Chapter</h2>
          <button className="modal__close" onClick={onClose}>✕</button>
        </div>
        <form className="new-chapter-modal__form" onSubmit={handleSubmit}>
          <label className="form-field">
            Chapter title
            <input
              autoFocus
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="Untitled Chapter"
            />
          </label>
          <div className="form-actions">
            <button type="button" className="btn btn--ghost" onClick={onClose}>Cancel</button>
            <button type="submit" className="btn btn--primary" disabled={createMutation.isPending}>
              {createMutation.isPending ? 'Creating…' : 'Create Chapter'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

// ─── Chapter List ─────────────────────────────────────────────────────────────

function ChapterList({
  chapters,
  currentChapterId,
  onSelect,
  projectId,
  onRefresh,
}: {
  chapters: Chapter[];
  currentChapterId: string | null;
  onSelect: (ch: Chapter) => void;
  projectId: string;
  onRefresh: () => void;
}) {
  const qc = useQueryClient();
  const addToast = useAppStore((s) => s.addToast);
  const [contextMenu, setContextMenu] = useState<{ chapterId: string; x: number; y: number } | null>(null);

  const deleteMutation = useMutation({
    mutationFn: (id: string) => chaptersApi.delete(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['chapters', projectId] });
      addToast({ type: 'success', message: 'Chapter deleted.' });
    },
    onError: () => addToast({ type: 'error', message: 'Failed to delete chapter.' }),
  });

  const handleContextMenu = (e: React.MouseEvent, chapterId: string) => {
    e.preventDefault();
    setContextMenu({ chapterId, x: e.clientX, y: e.clientY });
  };

  const closeMenu = () => setContextMenu(null);

  const handleDelete = (chapterId: string) => {
    const confirmed = window.confirm('Delete this chapter? This cannot be undone.');
    if (confirmed) deleteMutation.mutate(chapterId);
    closeMenu();
  };

  const handleRename = (chapterId: string, currentTitle: string) => {
    const newTitle = window.prompt('Rename chapter:', currentTitle);
    if (newTitle && newTitle.trim() !== currentTitle) {
      chaptersApi.update(chapterId, { title: newTitle.trim() }).then(() => {
        qc.invalidateQueries({ queryKey: ['chapters', projectId] });
        onRefresh();
      });
    }
    closeMenu();
  };

  if (chapters.length === 0) {
    return (
      <div className="empty-state empty-state--small">
        <p>No chapters yet.</p>
      </div>
    );
  }

  return (
    <>
      <ul className="chapter-list">
        {chapters.map((ch) => (
          <li
            key={ch.id}
            className={`chapter-list-item${currentChapterId === ch.id ? ' active' : ''}`}
            onClick={() => onSelect(ch)}
            onContextMenu={(e) => handleContextMenu(e, ch.id)}
            title={ch.title}
          >
            <span className="chapter-list-item__title">{ch.title}</span>
            <span className="chapter-list-item__words">{ch.word_count.toLocaleString()}</span>
          </li>
        ))}
      </ul>

      {contextMenu && (
        <>
          <div
            style={{ position: 'fixed', inset: 0, zIndex: 500 }}
            onClick={closeMenu}
          />
          <div
            style={{
              position: 'fixed',
              top: contextMenu.y,
              left: contextMenu.x,
              background: 'var(--bg-sidebar)',
              border: '1px solid var(--border-light)',
              borderRadius: 'var(--radius-md)',
              boxShadow: 'var(--shadow-md)',
              zIndex: 501,
              minWidth: 140,
              overflow: 'hidden',
            }}
          >
            {(() => {
              const ch = chapters.find((c) => c.id === contextMenu.chapterId);
              return ch ? (
                <>
                  <button
                    style={{ display: 'block', width: '100%', padding: '8px 14px', background: 'none', border: 'none', color: 'var(--text-primary)', fontFamily: 'var(--font-ui)', fontSize: 13, cursor: 'pointer', textAlign: 'left' }}
                    onClick={() => handleRename(ch.id, ch.title)}
                  >
                    Rename
                  </button>
                  <button
                    style={{ display: 'block', width: '100%', padding: '8px 14px', background: 'none', border: 'none', color: 'var(--danger)', fontFamily: 'var(--font-ui)', fontSize: 13, cursor: 'pointer', textAlign: 'left' }}
                    onClick={() => handleDelete(ch.id)}
                  >
                    Delete
                  </button>
                </>
              ) : null;
            })()}
          </div>
        </>
      )}
    </>
  );
}

// ─── Project Dashboard ────────────────────────────────────────────────────────

export function ProjectDashboard() {
  const { projectId } = useParams<{ projectId: string }>();
  const navigate = useNavigate();
  const qc = useQueryClient();
  const currentChapterId = useAppStore((s) => s.currentChapterId);
  const setCurrentChapter = useAppStore((s) => s.setCurrentChapter);
  const aiPanelOpen = useAppStore((s) => s.aiPanelOpen);
  const toggleAiPanel = useAppStore((s) => s.toggleAiPanel);
  const sidebarSection = useAppStore((s) => s.sidebarSection);
  const setSidebarSection = useAppStore((s) => s.setSidebarSection);

  const [showNewChapterModal, setShowNewChapterModal] = useState(false);
  const [editingProjectTitle, setEditingProjectTitle] = useState(false);
  const [projectTitle, setProjectTitle] = useState('');

  const { data: project } = useQuery({
    queryKey: ['project', projectId],
    queryFn: () => projectsApi.get(projectId!),
    enabled: !!projectId,
  });

  const { data: chapters = [], isLoading: chaptersLoading, refetch: refetchChapters } = useQuery({
    queryKey: ['chapters', projectId],
    queryFn: () => chaptersApi.listForProject(projectId!),
    enabled: !!projectId,
  });

  const currentChapter = chapters.find((ch) => ch.id === currentChapterId) || chapters[0];

  // Sync project title for inline editing
  useEffect(() => {
    if (project) setProjectTitle(project.title);
  }, [project]);

  // Auto-select first chapter
  useEffect(() => {
    if (chapters.length > 0 && !currentChapterId) {
      setCurrentChapter(chapters[0].id);
    }
  }, [chapters, currentChapterId, setCurrentChapter]);

  const handleSelectChapter = useCallback((ch: Chapter) => {
    setCurrentChapter(ch.id);
    navigate(`/project/${projectId}`);
  }, [projectId, setCurrentChapter, navigate]);

  const handleNewChapter = useCallback(() => {
    setShowNewChapterModal(true);
  }, []);

  const handleNewChapterCreated = useCallback(() => {
    refetchChapters();
  }, [refetchChapters]);

  const updateProjectTitle = useMutation({
    mutationFn: (title: string) => projectsApi.update(projectId!, { title }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['project', projectId] }),
  });

  const handleTitleBlur = () => {
    setEditingProjectTitle(false);
    if (project && projectTitle.trim() && projectTitle.trim() !== project.title) {
      updateProjectTitle.mutate(projectTitle.trim());
    }
  };

  const handleAiAction = useCallback((_mode: string) => {
    toggleAiPanel();
  }, [toggleAiPanel]);

  if (!projectId) {
    return <Navigate to="/" replace />;
  }

  const totalWords = chapters.reduce((sum, ch) => sum + ch.word_count, 0);

  return (
    <div className="project-dashboard">
      {/* Left Sidebar */}
      <aside className="chapter-sidebar">
        <div className="chapter-sidebar__header">
          <Link to="/" className="chapter-sidebar__back">
            ← Projects
          </Link>
          <span className="chapter-sidebar__title">
            {editingProjectTitle ? (
              <input
                autoFocus
                style={{
                  background: 'transparent',
                  border: 'none',
                  borderBottom: '1px solid var(--accent)',
                  color: 'var(--text-primary)',
                  fontFamily: 'var(--font-editorial)',
                  fontSize: 15,
                  fontWeight: 600,
                  width: '100%',
                  outline: 'none',
                  padding: '0 4px',
                }}
                value={projectTitle}
                onChange={(e) => setProjectTitle(e.target.value)}
                onBlur={handleTitleBlur}
                onKeyDown={(e) => e.key === 'Enter' && e.currentTarget.blur()}
              />
            ) : (
              <span
                style={{ cursor: 'pointer', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}
                onClick={() => setEditingProjectTitle(true)}
                title="Click to rename"
              >
                {project?.title || '…'}
              </span>
            )}
          </span>
        </div>

        <div className="chapter-sidebar__tabs">
          {(['chapters', 'companions', 'checkpoints'] as const).map((tab) => (
            <button
              key={tab}
              className={`chapter-sidebar__tab${sidebarSection === tab ? ' active' : ''}`}
              onClick={() => setSidebarSection(tab)}
            >
              {tab.charAt(0).toUpperCase() + tab.slice(1)}
            </button>
          ))}
        </div>

        <div className="chapter-sidebar__body">
          {sidebarSection === 'chapters' && (
            <div className="chapter-sidebar__section">
              {chaptersLoading ? (
                <div className="loading-state">Loading…</div>
              ) : (
                <ChapterList
                  chapters={chapters}
                  currentChapterId={currentChapterId}
                  onSelect={handleSelectChapter}
                  projectId={projectId}
                  onRefresh={() => refetchChapters()}
                />
              )}
              <button
                className="btn btn--ghost btn--small chapter-sidebar__add-btn"
                onClick={handleNewChapter}
              >
                + New Chapter
              </button>
            </div>
          )}
          {sidebarSection === 'companions' && (
            <div className="chapter-sidebar__section">
              <CompanionDocs />
            </div>
          )}
          {sidebarSection === 'checkpoints' && (
            <div className="chapter-sidebar__section">
              <CheckpointPanel chapterId={currentChapterId} />
            </div>
          )}
        </div>
      </aside>

      {/* Center Editor */}
      <main className="editor-area">
        <div className="editor-topbar">
          <span className="editor-topbar__title">{currentChapter?.title || 'No chapter selected'}</span>
          <div className="editor-topbar__right">
            <span className="editor-topbar__words">
              {totalWords.toLocaleString()} words
            </span>
            <button
              className={`btn btn--ghost btn--small`}
              onClick={toggleAiPanel}
              title="Toggle AI panel (⌘`)"
            >
              {aiPanelOpen ? 'AI ✕' : 'AI ◐'}
            </button>
          </div>
        </div>

        {currentChapter ? (
          <ChapterEditor
            key={currentChapter.id}
            chapter={currentChapter}
            projectId={projectId}
            onAiAction={handleAiAction}
          />
        ) : (
          <div className="empty-state" style={{ flex: 1 }}>
            <p>Select or create a chapter to start writing.</p>
            <button className="btn btn--primary" onClick={handleNewChapter}>
              + New Chapter
            </button>
          </div>
        )}
      </main>

      {/* Right AI Panel */}
      {aiPanelOpen && currentChapter && (
        <AIPanel
          projectId={projectId}
          chapterId={currentChapter.id}
          chapterContent={currentChapter.content}
        />
      )}

      {/* Toast notifications */}
      <ToastContainer />

      {/* Modals */}
      {showNewChapterModal && (
        <NewChapterModal
          projectId={projectId}
          onClose={() => setShowNewChapterModal(false)}
          onCreated={handleNewChapterCreated}
        />
      )}
    </div>
  );
}
