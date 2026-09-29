import { useCallback, useMemo, useState } from 'react';
import { ArrowLeft, BriefcaseBusiness, Building2, CalendarCheck, Copy, ExternalLink, FileText, Globe2, Heart, Mail, MapPin, Phone, Sparkles } from 'lucide-react';
import { Navigate, useNavigate, useParams } from 'react-router-dom';
import { useAppContext } from '../../app/app-context';
import { ScoreBadge } from '../../components/ScoreBadge';
import { AIModal } from '../../components/AIModal';
import { Toast } from '../../components/Toast';
import { ContactScoringForm } from '../contact-scoring/ContactScoringForm';
import { generateCompanyContent } from '../../services/scout/aiService';
import { maxBridge } from '../../services/max/maxBridge';
import type { CompanyStatus, GeneratedContent } from '../../types/scout';
import { STATUS_LABELS, formatDate } from '../../utils/format';
import { useMaxBackButton } from '../../hooks/useMaxBackButton';

export function CompanyPage() {
  const { companyId } = useParams();
  const navigate = useNavigate();
  const { employee, searchResponse, favorites, toggleFavorite, statusOverrides, setCompanyStatus } = useAppContext();
  const company = useMemo(() => {
    const found = searchResponse?.companies.find((item) => item.id === companyId);
    return found ? { ...found, status: statusOverrides[found.id] ?? found.status } : null;
  }, [companyId, searchResponse, statusOverrides]);
  const [modalOpen, setModalOpen] = useState(false);
  const [modalLoading, setModalLoading] = useState(false);
  const [generated, setGenerated] = useState<GeneratedContent | null>(null);
  const [copied, setCopied] = useState(false);
  const [toast, setToast] = useState('');
  const goBack = useCallback(() => navigate('/scout'), [navigate]);
  const contactQuery = company ? [company.name, company.inn || company.region, 'контакты телефон официальный сайт'].join(' ') : '';
  const contactSearchUrl = `https://yandex.ru/search/?text=${encodeURIComponent(contactQuery)}`;
  useMaxBackButton(goBack);

  if (!employee) return <Navigate to="/login" replace />;
  if (!company) return <Navigate to="/scout" replace />;

  const createContent = async (kind: 'offer' | 'script') => {
    setModalOpen(true);
    setModalLoading(true);
    setGenerated(null);
    setCopied(false);
    try {
      setGenerated(await generateCompanyContent(company, kind));
      maxBridge.notify('success');
    } finally {
      setModalLoading(false);
    }
  };

  const copyText = async (value: string, label = 'Скопировано') => {
    await navigator.clipboard.writeText(value);
    setToast(label);
    maxBridge.haptic('soft');
  };

  return (
    <main className="detail-page">
      <header className="detail-header">
        <button className="back-button" type="button" onClick={goBack}><ArrowLeft size={19} /> Назад к результатам</button>
        <button className={`icon-button icon-button--favorite ${favorites.includes(company.id) ? 'is-active' : ''}`} type="button" onClick={() => toggleFavorite(company.id)} aria-label="Избранное"><Heart size={20} fill={favorites.includes(company.id) ? 'currentColor' : 'none'} /></button>
      </header>

      <section className="company-hero">
        <div className="company-hero__identity"><div className="company-avatar company-avatar--large"><Building2 size={30} /></div><div><p className="eyebrow">{company.industry}</p><h1>{company.name}</h1><p><MapPin size={16} /> {company.region}</p></div></div>
        <ScoreBadge score={company.score} large />
      </section>

      <div className="detail-layout">
        <div className="detail-main">
          <section className="detail-card score-story">
            <div className="section-title"><div><p className="eyebrow">Почему стоит проверить</p><h2>Оценка приоритета</h2></div><Sparkles size={21} /></div>
            <p className="score-story__lead">{company.score.explanation}</p>
            <div className="reason-list">{company.reasons.map((reason, index) => <div key={reason}><span>0{index + 1}</span><p>{reason}</p></div>)}</div>
          </section>

          <section className="detail-card">
            <div className="section-title"><div><p className="eyebrow">Доказательная база</p><h2>Найденные сигналы</h2></div><CalendarCheck size={21} /></div>
            <div className="signals-list">{company.signals.map((signal) => <div key={signal}><span /><p>{signal}</p></div>)}</div>
          </section>

          <section className="detail-card">
            <div className="section-title"><div><p className="eyebrow">Контакт подтверждает гипотезу</p><h2>Результат первого контакта</h2></div><BriefcaseBusiness size={21} /></div>
            <p className="section-description">Ответьте на три вопроса — демонстрационный расчёт покажет, как может измениться приоритет.</p>
            <ContactScoringForm company={company} />
          </section>

          <section className="detail-card">
            <div className="section-title"><div><p className="eyebrow">Прозрачность данных</p><h2>Источники</h2></div><Globe2 size={21} /></div>
            <div className="source-list">{company.sources.map((source) => <div key={source.id}><div className="source-icon"><FileText size={18} /></div><div><strong>{source.url ? <a href={source.url} target="_blank" rel="noreferrer">{source.title} <ExternalLink size={13} /></a> : source.title}</strong><span>Данные от {formatDate(source.checkedAt)}</span></div><span className="source-type">{source.category === 'website' ? 'Сайт' : 'Реестр'}</span></div>)}</div>
          </section>
        </div>

        <aside className="detail-sidebar">
          <section className="detail-card contact-card">
            <p className="eyebrow">Реквизиты и контакты</p>
            {company.inn ? <div className="contact-row"><span><Building2 size={17} /> ИНН</span><button type="button" onClick={() => copyText(company.inn)}>{company.inn} <Copy size={14} /></button></div> : null}
            {company.phone ? <div className="contact-row"><span><Phone size={17} /> Телефон</span><button type="button" onClick={() => copyText(company.phone)}>{company.phone} <Copy size={14} /></button></div> : null}
            {company.email ? <div className="contact-row"><span><Mail size={17} /> Email</span><button type="button" onClick={() => copyText(company.email)}>{company.email} <Copy size={14} /></button></div> : null}
            {company.website ? <div className="contact-row"><span><Globe2 size={17} /> Сайт</span><button type="button" onClick={() => maxBridge.openExternal(company.website)}>Открыть <ExternalLink size={14} /></button></div> : null}
            <p className="section-description">Телефон и сайт показываются только при наличии источника. Перед звонком проверьте, что контакт относится к этому юридическому лицу.</p>
            <button className="text-button" type="button" onClick={() => maxBridge.openExternal(contactSearchUrl)}>Найти контакты по названию{company.inn ? ' и ИНН' : ''} <ExternalLink size={14} /></button>
          </section>
          <section className="detail-card status-card">
            <label htmlFor="company-status">Статус работы</label>
            <select id="company-status" value={company.status} onChange={(event) => { setCompanyStatus(company.id, event.target.value as CompanyStatus); setToast('Статус обновлён'); }}>
              {Object.entries(STATUS_LABELS).map(([value, label]) => <option value={value} key={value}>{label}</option>)}
            </select>
          </section>
          <section className="ai-actions">
            <p className="eyebrow">Следующий шаг · демо</p><h3>Подготовить контакт</h3><p>Пример оффера и скрипта по профилю компании.</p>
            <button className="button button--primary button--full" type="button" onClick={() => createContent('offer')}><Sparkles size={18} /> Создать оффер</button>
            <button className="button button--secondary button--full" type="button" onClick={() => createContent('script')}><FileText size={18} /> Создать скрипт</button>
          </section>
        </aside>
      </div>

      {modalOpen ? <AIModal content={generated} loading={modalLoading} onClose={() => setModalOpen(false)} copied={copied} onCopy={async () => { if (generated) { await navigator.clipboard.writeText(generated.body); setCopied(true); } }} /> : null}
      {toast ? <Toast message={toast} onClose={() => setToast('')} /> : null}
    </main>
  );
}
