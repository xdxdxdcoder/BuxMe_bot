import { useEffect, useState } from 'react';
import { Check, LoaderCircle } from 'lucide-react';

const isLiveMode = (import.meta.env.VITE_RUNTIME_MODE || import.meta.env.VITE_APP_MODE) === 'live';
const STEPS = isLiveMode
  ? ['Ищем компании', 'Читаем реестр ФНС', 'Анализируем подтверждённые признаки', 'Формируем рейтинг']
  : ['Готовим демо-компании', 'Показываем пример карточек', 'Формируем пример рейтинга'];

export function SearchProgress() {
  const [activeStep, setActiveStep] = useState(0);

  useEffect(() => {
    const interval = window.setInterval(() => setActiveStep((current) => Math.min(current + 1, STEPS.length - 1)), 620);
    return () => window.clearInterval(interval);
  }, []);

  return (
    <section className="search-progress" aria-live="polite">
      <div className="scan-orb"><div className="scan-orb__beam" /></div>
      <p className="eyebrow">AI-Scout работает</p>
      <h2>Собираем картину рынка</h2>
      <div className="progress-steps">
        {STEPS.map((step, index) => (
          <div className={`progress-step ${index <= activeStep ? 'progress-step--active' : ''}`} key={step}>
            <span>{index < activeStep ? <Check size={15} /> : <LoaderCircle size={15} />}</span>
            <p>{step}</p>
          </div>
        ))}
      </div>
      <div className="results-skeleton" aria-hidden="true">
        {[1, 2].map((item) => <div className="skeleton-card" key={item}><div /><div /><div /></div>)}
      </div>
    </section>
  );
}
