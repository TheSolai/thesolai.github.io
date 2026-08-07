import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { checkpointsApi } from '../lib/api';
import { useAppStore } from '../stores/appStore';

function formatRelativeTime(iso: string): string {
  const d = new Date(iso);
  const now = new Date();
  const diffMs = now.getTime() - d.getTime();
  const diffMins = Math.floor(diffMs / 60000);
  if (diffMins < 1) return 'Just now';
  if (diffMins < 60) return `${diffMins}m ago`;
  const diffHours = Math.floor(diffMins / 60);
  if (diffHours < 24) return `${diffHours}h ago`;
  const diffDays = Math.floor(diffHours / 24);
  if (diffDays < 7) return `${diffDays}d ago`;
  return d.toLocaleDateString();
}

interface CheckpointPanelProps {
  chapterId: string | null;
}

export function CheckpointPanel({ chapterId }: CheckpointPanelProps) {
  const qc = useQueryClient();
  const addToast = useAppStore((s) => s.addToast);
  const [confirmDelete, setConfirmDelete] = useState<string | null>(null);

  const {
    data: checkpoints = [],
    isLoading,
    isError,
  } = useQuery({
    queryKey: ['checkpoints', chapterId],
    queryFn: () => checkpointsApi.listForChapter(chapterId!),
    enabled: !!chapterId,
  });

  const createMutation = useMutation({
    mutationFn: (name: string) => checkpointsApi.create(chapterId!, name),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['checkpoints', chapterId] });
      addToast({ type: 'success', message: 'Checkpoint created.' });
    },
    onError: () => addToast({ type: 'error', message: 'Failed to create checkpoint.' }),
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => checkpointsApi.delete(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['checkpoints', chapterId] });
      setConfirmDelete(null);
      addToast({ type: 'success', message: 'Checkpoint deleted.' });
    },
    onError: () => addToast({ type: 'error', message: 'Failed to delete checkpoint.' }),
  });

  const restoreMutation = useMutation({
    mutationFn: (cpid: string) => checkpointsApi.restore(chapterId!, cpid),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['chapters'] });
      addToast({ type: 'success', message: 'Chapter restored from checkpoint.' });
    },
    onError: () => addToast({ type: 'error', message: 'Failed to restore checkpoint.' }),
  });

  const handleCreate = () => {
    const name = window.prompt('Checkpoint name:');
    if (name && name.trim()) {
      createMutation.mutate(name.trim());
    }
  };

  const handleRestore = (cpid: string, name: string) => {
    const confirmed = window.confirm(
      `Restore checkpoint "${name}"?\n\nThis will overwrite the current chapter content. Continue?`,
    );
    if (confirmed) {
      restoreMutation.mutate(cpid);
    }
  };

  if (!chapterId) {
    return (
      <div className="checkpoint-panel">
        <div className="empty-state empty-state--small">
          <p>Select a chapter to manage checkpoints.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="checkpoint-panel">
      <div className="checkpoint-panel__header">
        <h3 className="checkpoint-panel__title">Checkpoints</h3>
        <button
          className="btn btn--primary btn--small"
          onClick={handleCreate}
          disabled={createMutation.isPending}
        >
          + New
        </button>
      </div>

      {isLoading ? (
        <div className="loading-state">Loading checkpoints…</div>
      ) : isError ? (
        <div className="empty-state empty-state--small">
          <p>Failed to load checkpoints.</p>
        </div>
      ) : checkpoints.length === 0 ? (
        <div className="empty-state empty-state--small">
          <p>No checkpoints yet.</p>
          <button className="btn btn--ghost btn--small" onClick={handleCreate}>
            Save First Checkpoint
          </button>
        </div>
      ) : (
        <ul className="checkpoint-list">
          {checkpoints.map((cp) => (
            <li key={cp.id} className="checkpoint-item">
              <div className="checkpoint-item__info">
                <span className="checkpoint-item__name">{cp.name}</span>
                <span className="checkpoint-item__meta">
                  {cp.word_count.toLocaleString()} words · {formatRelativeTime(cp.created_at)}
                </span>
              </div>
              <div className="checkpoint-item__actions">
                {confirmDelete === cp.id ? (
                  <>
                    <button
                      className="btn btn--danger btn--small"
                      onClick={() => deleteMutation.mutate(cp.id)}
                      disabled={deleteMutation.isPending}
                    >
                      Confirm
                    </button>
                    <button
                      className="btn btn--ghost btn--small"
                      onClick={() => setConfirmDelete(null)}
                    >
                      Cancel
                    </button>
                  </>
                ) : (
                  <>
                    <button
                      className="btn btn--ghost btn--small"
                      onClick={() => handleRestore(cp.id, cp.name)}
                      disabled={restoreMutation.isPending}
                    >
                      Restore
                    </button>
                    <button
                      className="btn btn--ghost btn--small btn--danger"
                      onClick={() => setConfirmDelete(cp.id)}
                    >
                      Delete
                    </button>
                  </>
                )}
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
