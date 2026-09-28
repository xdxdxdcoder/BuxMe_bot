import { ArrowUpRight, Building2, Heart, MapPin } from 'lucide-react';
import type { Company } from '../../types/scout';
import { STATUS_LABELS } from '../../utils/format';
import { ScoreBadge } from '../../components/ScoreBadge';

interface CompanyCardProps {
  company: Company;
  favorite: boolean;
  onToggleFavorite: () => void;
  onOpen: () => void;
}

export function CompanyCard({ company, favorite, onToggleFavorite, onOpen }: CompanyCardProps) {
  return (
    <article className="company-card">
      <div className="company-card__top">
        <div className="company-card__identity">
          <div className="company-avatar"><Building2 size={21} /></div>
          <div>
            <p className="company-card__industry">{company.industry}</p>
            <h3>{company.name}</h3>
          </div>
        </div>
        <button
          className={`icon-button icon-button--favorite ${favorite ? 'is-active' : ''}`}
          type="button"
          onClick={onToggleFavorite}
          aria-label={favorite ? 'Убрать из избранного' : 'Добавить в избранное'}
        >
          <Heart size={19} fill={favorite ? 'currentColor' : 'none'} />
        </button>
      </div>
      <div className="company-card__meta"><MapPin size={15} /><span>{company.region}</span>{company.employeesRange ? <><span>·</span><span>{company.employeesRange} чел.</span></> : null}</div>
      <div className="company-card__score"><ScoreBadge score={company.score} /></div>
      <p className="company-card__explanation">{company.score.explanation}</p>
      <div className="signal-chips">
        {company.signals.slice(0, 2).map((signal) => <span key={signal}>{signal}</span>)}
      </div>
      <div className="company-card__footer">
        <span className={`status-pill status-pill--${company.status}`}>{STATUS_LABELS[company.status]}</span>
        <button className="text-button" type="button" onClick={onOpen}>Подробнее <ArrowUpRight size={17} /></button>
      </div>
    </article>
  );
}
