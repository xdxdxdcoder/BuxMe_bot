import { useState } from 'react';
import { ArrowRight, CheckCircle2, LoaderCircle, RotateCcw } from 'lucide-react';
import type { Company, ContactResult, ScoreRecalculation } from '../../types/scout';
import { recalculateScore } from '../../services/scout/aiService';
import { maxBridge } from '../../services/max/maxBridge';

const QUESTIONS: Array<{ key: keyof Pick<ContactResult, 'reachedDecisionMaker' | 'hasFieldTeam' | 'automationInterest'>; label: string }> = [
  { key: 'reachedDecisionMaker', label: 'Удалось связаться с ответственным лицом?' },
  { key: 'hasFieldTeam', label: 'Есть ли у компании полевые сотрудники?' },
  { key: 'automationInterest', label: 'Есть ли интерес к автоматизации команды?' },
];

const OPTIONS: Array<{ value: 'yes' | 'no' | 'unknown'; label: string }> = [
  { value: 'yes', label: 'Да' },
  { value: 'no', label: 'Нет' },
  { value: 'unknown', label: 'Неясно' },
];

const EMPTY_RESULT: ContactResult = {
  reachedDecisionMaker: 'unknown',
  hasFieldTeam: 'unknown',
  automationInterest: 'unknown',
};

export function ContactScoringForm({ company }: { company: Company }) {
  const [result, setResult] = useState<ContactResult>(EMPTY_RESULT);
  const [recalculation, setRecalculation] = useState<ScoreRecalculation | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async () => {
    setLoading(true);
    try {
      setRecalculation(await recalculateScore(company, result));
      maxBridge.notify('success');
    } finally {
      setLoading(false);
    }
  };

  if (recalculation) {
    return (
      <div className="recalculation-result">
        <CheckCircle2 size={24} />
        <p className="eyebrow">Демо-пересчёт рейтинга</p>
        <div className="score-change"><span>{recalculation.previousScore}/100</span><ArrowRight /><strong>{recalculation.newScore}/100</strong></div>
        <p>{recalculation.explanation}</p>
        <button className="text-button" type="button" onClick={() => setRecalculation(null)}><RotateCcw size={16} /> Изменить ответы</button>
      </div>
    );
  }

  return (
    <div className="contact-form">
      {QUESTIONS.map((question, index) => (
        <fieldset key={question.key}>
          <legend><span>0{index + 1}</span>{question.label}</legend>
          <div className="segmented-control">
            {OPTIONS.map((option) => (
              <button
                className={result[question.key] === option.value ? 'is-selected' : ''}
                type="button"
                key={option.value}
                onClick={() => setResult((current) => ({ ...current, [question.key]: option.value }))}
              >
                {option.label}
              </button>
            ))}
          </div>
        </fieldset>
      ))}
      <label className="field-label" htmlFor="contact-notes">Заметка после звонка <span>необязательно</span></label>
      <textarea id="contact-notes" placeholder="Коротко зафиксируйте детали разговора" value={result.notes ?? ''} onChange={(event) => setResult((current) => ({ ...current, notes: event.target.value }))} />
      <button className="button button--primary button--full" type="button" onClick={handleSubmit} disabled={loading}>
        {loading ? <LoaderCircle className="spin" size={18} /> : null}Пересчитать рейтинг
      </button>
    </div>
  );
}
