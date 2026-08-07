import { useEffect } from 'react';
import { useAppStore } from '../stores/appStore';

const ICONS: Record<string, string> = {
  success: '✓',
  error: '✕',
  info: 'ℹ',
};

function ToastItem({ id, type, message }: { id: string; type: 'success' | 'error' | 'info'; message: string }) {
  const removeToast = useAppStore((s) => s.removeToast);

  useEffect(() => {
    const timer = setTimeout(() => removeToast(id), 4000);
    return () => clearTimeout(timer);
  }, [id, removeToast]);

  return (
    <div className={`toast toast--${type}`} role="alert">
      <div className="toast__icon">{ICONS[type]}</div>
      <p className="toast__message">{message}</p>
      <button
        className="toast__close"
        onClick={() => removeToast(id)}
        aria-label="Dismiss"
      >
        ✕
      </button>
    </div>
  );
}

export function ToastContainer() {
  const toasts = useAppStore((s) => s.toasts);

  if (toasts.length === 0) return null;

  return (
    <div className="toast-container" aria-live="polite">
      {toasts.map((toast) => (
        <ToastItem key={toast.id} {...toast} />
      ))}
    </div>
  );
}
