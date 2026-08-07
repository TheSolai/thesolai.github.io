import { useCallback, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { aiApi } from '../lib/api';
import { useAIStore, useAppStore } from '../stores/appStore';

type AIMode = 'feedback' | 'copyedit' | 'format' | 'revision';

const MODE_LABELS: Record<AIMode, string> = {
  feedback: 'Feedback',
  copyedit: 'Copyedit',
  format: 'Format Check',
  revision: 'Revision',
};

function stripHtml(html: string): string {
  const tmp = document.createElement('div');
  tmp.innerHTML = html;
  return tmp.textContent || tmp.innerText || '';
}

export function AIPanel({ projectId, chapterId, chapterContent }: { projectId: string; chapterId: string; chapterContent: string }) {
  const store = useAIStore();
  const addToast = useAppStore((s) => s.addToast);

  const { data: personas = [] } = useQuery({
    queryKey: ['ai-personas'],
    queryFn: aiApi.personas,
  });

  const { data: aiSettings } = useQuery({
    queryKey: ['ai-settings'],
    queryFn: aiApi.settings,
    staleTime: Infinity,
  });

  // Sync model from settings on load
  useEffect(() => {
    if (aiSettings?.ai_model && !store.selectedModelId) {
      store.setModel(aiSettings.ai_model);
    }
  }, [aiSettings]);

  const { data: allModels = [] } = useQuery({
    queryKey: ['ai-status'],
    queryFn: aiApi.status,
    staleTime: 60_000,
  });

  const handleModelChange = useCallback(async (modelId: string) => {
    store.setModel(modelId);
    try {
      await aiApi.updateSettings({ ai_model: modelId });
      addToast({ type: 'success', message: `Model: ${modelId}` });
    } catch {
      addToast({ type: 'error', message: 'Failed to save model preference' });
    }
  }, [store, addToast]);

  const sendRequest = useCallback(async () => {
    const passage = store.selectedPassage || stripHtml(chapterContent);
    if (!passage.trim()) {
      addToast({ type: 'info', message: 'No content to review.' });
      return;
    }
    store.setLoading(true);
    store.setResponse('');
    store.setAnnotations([]);
    try {
      let resp;
      const base = { project_id: projectId, chapter_id: chapterId, passage };
      switch (store.activeMode as AIMode) {
        case 'feedback':
          resp = await aiApi.feedback({ ...base, persona_id: store.selectedPersonaId || undefined });
          break;
        case 'copyedit':
          resp = await aiApi.copyedit({ ...base, persona_id: store.selectedPersonaId || undefined });
          break;
        case 'format':
          resp = await aiApi.formatCheck(base);
          break;
        case 'revision':
          resp = await aiApi.revisionPass({ ...base, persona_id: store.selectedPersonaId || undefined });
          break;
      }
      store.setResponse(resp.summary || resp.feedback || resp.report || resp.revision_guide || '');
      store.setAnnotations(
        (resp.annotations || []).map((a: { start: number; end: number; type: string; message: string; suggestion?: string }) => ({ ...a, dismissed: false })),
      );
      addToast({ type: 'success', message: `${MODE_LABELS[store.activeMode as AIMode]} complete.` });
    } catch {
      store.setResponse('An error occurred while processing your request.');
      addToast({ type: 'error', message: 'AI request failed.' });
    } finally {
      store.setLoading(false);
    }
  }, [projectId, chapterId, chapterContent, store, addToast]);

  const applySuggestion = (idx: number, suggestion?: string) => {
    store.dismissAnnotation(idx);
    if (suggestion) {
      addToast({ type: 'info', message: 'Suggestion noted.' });
    }
  };

  if (!useAppStore((s) => s.aiPanelOpen)) return null;

  const currentModel = store.selectedModelId || aiSettings?.ai_model || 'llama2-uncensored:latest';

  return (
    <aside className="ai-panel">
      <div className="ai-panel__header">
        <h2 className="ai-panel__title">Editorial AI</h2>
        <button className="ai-panel__close" onClick={() => useAppStore.getState().toggleAiPanel()}>
          ✕
        </button>
      </div>

      <div className="ai-panel__model-selector">
        <label className="form-field form-field--inline">
          <span className="form-field__label">Model</span>
          <select
            value={currentModel}
            onChange={(e) => handleModelChange(e.target.value)}
            className="form-field__select"
            title="Switch AI model on the fly"
          >
            {allModels.map((model: string) => {
              const isMLX = model.toLowerCase().includes('mlx');
              const isUncensored = /uncensored|abliterated|dolphin/i.test(model);
              const gbMatch = allModels.find((m: string) => m === model);
              return (
                <option key={model} value={model}>
                  {model}
                  {isMLX ? ' ★' : ''}
                  {isUncensored ? ' ★' : ''}
                </option>
              );
            })}
          </select>
        </label>
      </div>

      <div className="ai-panel__persona">
        <label className="form-field form-field--inline">
          <span className="form-field__label">Persona</span>
          <select
            value={store.selectedPersonaId}
            onChange={(e) => store.setPersona(e.target.value)}
          >
            <option value="">Default</option>
            {personas.map((p: { id: string; name: string }) => (
              <option key={p.id} value={p.id}>
                {p.name}
              </option>
            ))}
          </select>
        </label>
      </div>

      <div className="ai-panel__tabs" role="tablist">
        {(Object.keys(MODE_LABELS) as AIMode[]).map((mode) => (
          <button
            key={mode}
            role="tab"
            aria-selected={store.activeMode === mode}
            className={`ai-panel__tab${store.activeMode === mode ? ' active' : ''}`}
            onClick={() => store.setMode(mode)}
          >
            {MODE_LABELS[mode]}
          </button>
        ))}
      </div>

      <div className="ai-panel__passage">
        <label className="ai-panel__label">
          {store.selectedPassage ? 'Selected passage' : 'Full chapter'}
        </label>
        <div className="ai-panel__passage-box">
          {(store.selectedPassage || stripHtml(chapterContent)).slice(0, 500)}
          {(store.selectedPassage || chapterContent).length > 500 ? '…' : ''}
        </div>
      </div>

      <button
        className="btn btn--primary ai-panel__send"
        onClick={sendRequest}
        disabled={store.isLoading}
      >
        {store.isLoading ? 'Processing…' : `Send for ${MODE_LABELS[store.activeMode as AIMode]}`}
      </button>

      {store.isLoading && (
        <div className="ai-panel__loading">
          <span className="spinner" />
          <span>Analyzing with {currentModel}…</span>
        </div>
      )}

      {store.response && !store.isLoading && (
        <div className="ai-panel__response">
          <label className="ai-panel__label">
            Response
            <span className="ai-panel__model-tag" title="Active model">
              {currentModel}
            </span>
          </label>
          <div className="ai-panel__response-text">{store.response}</div>
        </div>
      )}

      {store.annotations.length > 0 && !store.isLoading && (
        <div className="ai-panel__annotations">
          <label className="ai-panel__label">
            Annotations ({store.annotations.filter((a: { dismissed?: boolean }) => !a.dismissed).length})
          </label>
          {store.annotations.map((ann: { start: number; end: number; type: string; message: string; suggestion?: string; dismissed?: boolean }, idx: number) => (
            <div key={idx} className={`annotation-card${ann.dismissed ? ' dismissed' : ''}`}>
              <div className="annotation-card__header">
                <span className={`annotation-badge annotation-badge--${ann.type}`}>
                  {ann.type}
                </span>
              </div>
              <p className="annotation-card__message">{ann.message}</p>
              {ann.suggestion && !ann.dismissed && (
                <div className="annotation-card__suggestion">
                  <code>{ann.suggestion}</code>
                </div>
              )}
              {!ann.dismissed && (
                <div className="annotation-card__actions">
                  {ann.suggestion && (
                    <button
                      className="btn btn--ghost btn--small"
                      onClick={() => applySuggestion(idx, ann.suggestion)}
                    >
                      Apply
                    </button>
                  )}
                  <button
                    className="btn btn--ghost btn--small"
                    onClick={() => store.dismissAnnotation(idx)}
                  >
                    Dismiss
                  </button>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </aside>
  );
}
