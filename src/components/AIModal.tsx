import { Check, Copy, Sparkles, X } from 'lucide-react';
import type { GeneratedContent } from '../types/scout';

interface AIModalProps {
  content: GeneratedContent | null;
  loading: boolean;
  onClose: () => void;
  onCopy: () => void;
  copied: boolean;
}

export function AIModal({ content, loading, onClose, onCopy, copied }: AIModalProps) {
  return (
    <div className="modal-backdrop" role="presentation" onMouseDown={onClose}>
      <section className="modal-card" role="dialog" aria-modal="true" aria-label="Шаблон для контакта" onMouseDown={(event) => event.stopPropagation()}>
        <div className="modal-card__header">
          <div className="modal-card__icon"><Sparkles size={20} /></div>
          <button className="icon-button" type="button" onClick={onClose} aria-label="Закрыть"><X size={20} /></button>
        </div>
        {loading ? (
          <div className="modal-loading">
            <div className="skeleton skeleton--title" />
            <div className="skeleton skeleton--line" />
            <div className="skeleton skeleton--line" />
            <div className="skeleton skeleton--line-short" />
          </div>
        ) : content ? (
          <>
            <p className="eyebrow">Шаблон · демо</p>
            <h2>{content.title}</h2>
            <p className="generated-copy">{content.body}</p>
            <button className="button button--secondary button--full" type="button" onClick={onCopy}>
              {copied ? <Check size={18} /> : <Copy size={18} />}
              {copied ? 'Скопировано' : 'Скопировать текст'}
            </button>
          </>
        ) : null}
      </section>
    </div>
  );
}
