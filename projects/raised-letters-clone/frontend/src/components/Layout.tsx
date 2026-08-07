import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { projectsApi, Project } from '../lib/api';
import { useAppStore } from '../stores/appStore';

// ─── Project Card ────────────────────────────────────────────────────────────

function formatDate(iso: string): string {
  const d = new Date(iso);
  const now = new Date();
  const diff = Math.floor((now.getTime() - d.getTime()) / 86400000);
  if (diff === 0) return 'Today';
  if (diff === 1) return 'Yesterday';
  if (diff < 7) return `${diff} days ago`;
  if (diff < 30) return `${Math.floor(diff / 7)} weeks ago`;
  return d.toLocaleDateString();
}

export function ProjectCard({ project }: { project: Project }) {
  const navigate = useNavigate();

  return (
    <div
      className="project-card"
      onClick={() => navigate(`/project/${project.id}`)}
    >
      <div className="project-card__genre">{project.genre || 'Untagged'}</div>
      <h2 className="project-card__title">{project.title}</h2>
      {project.author && (
        <p className="project-card__author">by {project.author}</p>
      )}
      <p className="project-card__meta">
        {project.chapter_count ?? 0} chapters · {project.word_count ?? 0} words
      </p>
      <p className="project-card__date">
        Last edited: {formatDate(project.updated_at)}
      </p>
      <button className="project-card__cta">Continue Writing →</button>
    </div>
  );
}

// ─── New Project Modal ────────────────────────────────────────────────────────

const GENRES = [
  'Literary Fiction', 'Thriller', 'Sci-Fi', 'Non-Fiction',
  'Fantasy', 'Horror', 'Romance', 'Other',
];

export function NewProjectModal({ onClose }: { onClose: () => void }) {
  const qc = useQueryClient();
  const addToast = useAppStore((s) => s.addToast);
  const [title, setTitle] = useState('');
  const [author, setAuthor] = useState('');
  const [genre, setGenre] = useState('');
  const [subtitle, setSubtitle] = useState('');

  const create = useMutation({
    mutationFn: (data: Partial<Project>) => projectsApi.create(data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['projects'] });
      addToast({ type: 'success', message: 'Project created' });
      onClose();
    },
    onError: () => addToast({ type: 'error', message: 'Failed to create project' }),
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim()) return;
    create.mutate({ title: title.trim(), author, genre, subtitle });
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        <div className="modal__header">
          <h2>New Manuscript</h2>
          <button className="modal__close" onClick={onClose}>✕</button>
        </div>
        <form onSubmit={handleSubmit} className="modal__body">
          <label className="form-field">
            Title <span className="required">*</span>
            <input
              autoFocus
              type="text"
              placeholder="Untitled Manuscript"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              required
            />
          </label>
          <label className="form-field">
            Author
            <input
              type="text"
              placeholder="Your name"
              value={author}
              onChange={(e) => setAuthor(e.target.value)}
            />
          </label>
          <label className="form-field">
            Genre
            <select value={genre} onChange={(e) => setGenre(e.target.value)}>
              <option value="">Select genre…</option>
              {GENRES.map((g) => (
                <option key={g} value={g}>{g}</option>
              ))}
            </select>
          </label>
          <label className="form-field">
            Subtitle
            <input
              type="text"
              placeholder="Optional subtitle"
              value={subtitle}
              onChange={(e) => setSubtitle(e.target.value)}
            />
          </label>
          <div className="modal__actions">
            <button type="button" className="btn btn--ghost" onClick={onClose}>Cancel</button>
            <button type="submit" className="btn btn--primary" disabled={create.isPending}>
              {create.isPending ? 'Creating…' : 'Create Project'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

// ─── Project List Page ────────────────────────────────────────────────────────

export function ProjectListPage() {
  const [showModal, setShowModal] = useState(false);

  const { data: projects = [], isLoading } = useQuery({
    queryKey: ['projects'],
    queryFn: projectsApi.list,
  });

  return (
    <div className="project-list-page">
      <header className="project-list-page__header">
        <div>
          <h1 className="project-list-page__logo">Raised Letters</h1>
          <p className="project-list-page__tagline">A writing environment for authors</p>
        </div>
        <button className="btn btn--primary" onClick={() => setShowModal(true)}>
          + New Manuscript
        </button>
      </header>

      {isLoading ? (
        <div className="loading-state">Loading your manuscripts…</div>
      ) : projects.length === 0 ? (
        <div className="empty-state">
          <p>Your manuscripts will appear here.</p>
          <button className="btn btn--primary btn--large" onClick={() => setShowModal(true)}>
            Start Writing
          </button>
        </div>
      ) : (
        <div className="project-grid">
          {projects.map((p) => (
            <ProjectCard key={p.id} project={p} />
          ))}
        </div>
      )}

      {showModal && <NewProjectModal onClose={() => setShowModal(false)} />}
    </div>
  );
}
