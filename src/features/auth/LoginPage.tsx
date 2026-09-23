import { useState, type FormEvent } from 'react';
import { ArrowRight, LoaderCircle, ShieldCheck, Sparkles } from 'lucide-react';
import { Navigate, useNavigate } from 'react-router-dom';
import { BrandMark } from '../../components/BrandMark';
import { useAppContext } from '../../app/app-context';
import { authService } from '../../services/auth/authService';
import { maxBridge } from '../../services/max/maxBridge';

export function LoginPage() {
  const { employee, setEmployee } = useAppContext();
  const navigate = useNavigate();
  const [code, setCode] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  if (employee) return <Navigate to="/scout" replace />;

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    if (!code.trim()) {
      setError('Введите код сотрудника, чтобы продолжить');
      maxBridge.notify('error');
      return;
    }

    setLoading(true);
    setError('');
    try {
      setEmployee(await authService.authenticate(code.trim()));
      maxBridge.notify('success');
      navigate('/scout', { replace: true });
    } catch {
      setError('Не удалось выполнить вход. Попробуйте ещё раз.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="login-page">
      <section className="login-visual" aria-label="Buxme — Break the rules">
        <img src="/brand/buxme.jpg" alt="Buxme — Break the rules" />
        <div className="login-visual__shade" />
        <div className="login-visual__content">
          <span className="live-pill"><span /> AI sales intelligence</span>
          <p>Находите точки роста раньше, чем их заметит рынок.</p>
        </div>
      </section>
      <section className="login-panel">
        <div className="login-panel__top"><BrandMark /><span className="product-chip"><Sparkles size={14} /> AI-SCOUT</span></div>
        <div className="login-panel__body">
          <p className="eyebrow">Платформа Buxme</p>
          <h1>Интеллектуальный поиск потенциальных клиентов</h1>
          <p className="lead">AI-Scout находит компании с полевыми командами и объясняет, почему с ними стоит связаться.</p>
          <form onSubmit={handleSubmit} noValidate>
            <label className="field-label" htmlFor="employee-code">Код сотрудника</label>
            <div className={`input-wrap ${error ? 'input-wrap--error' : ''}`}>
              <input id="employee-code" value={code} onChange={(event) => { setCode(event.target.value); setError(''); }} placeholder="Например, BUX-2048" autoComplete="off" autoFocus />
              <ShieldCheck size={19} />
            </div>
            {error ? <p className="field-error" role="alert">{error}</p> : <p className="field-help">Демо-режим: подойдёт любой непустой код</p>}
            <button className="button button--primary button--full" type="submit" disabled={loading}>
              {loading ? <LoaderCircle className="spin" size={19} /> : <>Войти <ArrowRight size={19} /></>}
            </button>
          </form>
        </div>
        <p className="login-panel__footer">Secure workspace · Mock authentication</p>
      </section>
    </main>
  );
}
