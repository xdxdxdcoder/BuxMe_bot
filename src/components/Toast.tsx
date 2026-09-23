import { CheckCircle2, X } from 'lucide-react';

export function Toast({ message, onClose }: { message: string; onClose: () => void }) {
  return (
    <div className="toast" role="status">
      <CheckCircle2 size={18} />
      <span>{message}</span>
      <button type="button" onClick={onClose} aria-label="Закрыть уведомление">
        <X size={16} />
      </button>
    </div>
  );
}
