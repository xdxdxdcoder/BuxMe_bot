import { useMemo, useState, type FormEvent } from 'react';
import { ArrowRight, ChevronDown, Clock3, Heart, LogOut, Search, SlidersHorizontal, Sparkles } from 'lucide-react';
import { Navigate, useNavigate } from 'react-router-dom';
import { useAppContext } from '../../app/app-context';
import { BrandMark } from '../../components/BrandMark';
import { CompanyCard } from '../company/CompanyCard';
import { SearchProgress } from './SearchProgress';
import { searchCompanies } from '../../services/scout/scoutService';
import { maxBridge } from '../../services/max/maxBridge';
import type { Company } from '../../types/scout';

type SortMode = 'score' | 'name';

export function ScoutPage() {
  const navigate = useNavigate();
  const {
    employee,
    setEmployee,
    searchResponse,
    setSearchResponse,
    favorites,
    toggleFavorite,
    recentRegions,
    addRecentRegion,
    statusOverrides,
  } = useAppContext();
  const [region, setRegion] = useState('');
  const [query, setQuery] = useState('');
  const [minScore, setMinScore] = useState(0);
  const [sort, setSort] = useState<SortMode>('score');
  const [onlyFavorites, setOnlyFavorites] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const companies = useMemo(() => {
    const updated = (searchResponse?.companies ?? []).map((company) => ({
      ...company,
      status: statusOverrides[company.id] ?? company.status,
    }));
    return updated
      .filter((company) => company.score.value >= minScore)
      .filter((company) => !onlyFavorites || favorites.includes(company.id))
      .filter((company) => `${company.name} ${company.industry}`.toLowerCase().includes(query.toLowerCase()))
      .sort((left, right) => (sort === 'score' ? right.score.value - left.score.value : left.name.localeCompare(right.name, 'ru')));
  }, [favorites, minScore, onlyFavorites, query, searchResponse, sort, statusOverrides]);

  if (!employee) return <Navigate to="/login" replace />;

  const handleSearch = async (event: FormEvent) => {
    event.preventDefault();
    if (!region.trim()) {
      setError('Укажите регион или город');
      maxBridge.notify('error');
      return;
    }
    setLoading(true);
    setError('');
    try {
      const response = await searchCompanies(region.trim());
      setSearchResponse(response);
      addRecentRegion(region.trim());
      maxBridge.notify('success');
    } catch {
      setError('Поиск временно недоступен. Проверьте соединение и повторите попытку.');
    } finally {
      setLoading(false);
    }
  };

  const openCompany = (company: Company) => navigate(`/company/${company.id}`);

  return (
    <main className="app-shell">
      <header className="app-header">
        <div className="app-header__brand"><BrandMark compact /><span>AI-SCOUT</span></div>
        <div className="app-header__profile">
          <div className="profile-copy"><strong>{employee.displayName}</strong><span>{employee.code}</span></div>
          {employee.avatarUrl ? <img src={employee.avatarUrl} alt="" /> : <div className="profile-avatar">{employee.displayName.charAt(0)}</div>}
          <button className="icon-button" type="button" onClick={() => setEmployee(null)} aria-label="Выйти"><LogOut size={18} /></button>
        </div>
      </header>

      <section className="hero-search">
        <div className="hero-search__copy">
          <span className="live-pill"><span /> AI-powered lead discovery</span>
          <h1>Находим компании,<br /><em>готовые к росту</em></h1>
          <p>Ищем бизнесы с полевыми торговыми представителями и превращаем открытые сигналы в понятный приоритет.</p>
        </div>
        <form className="search-box" onSubmit={handleSearch} noValidate>
          <label htmlFor="region">Регион или город</label>
          <div className={`search-box__input ${error ? 'input-wrap--error' : ''}`}>
            <Search size={22} />
            <input id="region" placeholder="Например, Краснодарский край" value={region} onChange={(event) => { setRegion(event.target.value); setError(''); }} />
            <button className="button button--primary" type="submit">Найти компании <ArrowRight size={18} /></button>
          </div>
          {error ? <p className="field-error" role="alert">{error}</p> : null}
          {recentRegions.length ? (
            <div className="recent-regions"><Clock3 size={15} /><span>Недавние:</span>{recentRegions.map((item) => <button type="button" key={item} onClick={() => setRegion(item)}>{item}</button>)}</div>
          ) : null}
        </form>
      </section>

      {loading ? <SearchProgress /> : searchResponse ? (
        <section className="results-section">
          <div className="results-heading">
            <div>
              <p className="eyebrow">Результат сканирования</p>
              <h2>{searchResponse.total} компании в фокусе</h2>
              <p>Регион: {searchResponse.region} · Демо-данные</p>
            </div>
            <div className="results-heading__metric"><Sparkles size={18} /><span>Средний AI Score</span><strong>{Math.round(searchResponse.companies.reduce((sum, company) => sum + company.score.value, 0) / searchResponse.total)}%</strong></div>
          </div>

          <div className="filter-bar">
            <div className="filter-search"><Search size={17} /><input aria-label="Поиск среди результатов" placeholder="Поиск по компаниям" value={query} onChange={(event) => setQuery(event.target.value)} /></div>
            <button className={`filter-button ${onlyFavorites ? 'is-active' : ''}`} type="button" onClick={() => setOnlyFavorites((value) => !value)}><Heart size={16} /> Избранное</button>
            <label className="filter-select"><SlidersHorizontal size={16} /><span>Score от</span><select value={minScore} onChange={(event) => setMinScore(Number(event.target.value))}><option value="0">0%</option><option value="70">70%</option><option value="80">80%</option><option value="90">90%</option></select><ChevronDown size={15} /></label>
            <label className="filter-select"><span>Сначала</span><select value={sort} onChange={(event) => setSort(event.target.value as SortMode)}><option value="score">сильные</option><option value="name">по названию</option></select><ChevronDown size={15} /></label>
          </div>

          {companies.length ? (
            <div className="company-grid">
              {companies.map((company) => (
                <CompanyCard key={company.id} company={company} favorite={favorites.includes(company.id)} onToggleFavorite={() => { toggleFavorite(company.id); maxBridge.haptic('soft'); }} onOpen={() => openCompany(company)} />
              ))}
            </div>
          ) : (
            <div className="empty-state"><Search size={28} /><h3>Ничего не найдено</h3><p>Сбросьте фильтры или измените поисковый запрос.</p><button className="text-button" type="button" onClick={() => { setQuery(''); setMinScore(0); setOnlyFavorites(false); }}>Сбросить фильтры</button></div>
          )}
        </section>
      ) : (
        <section className="presearch-state">
          <div className="presearch-state__grid">
            <div><span>01</span><h3>Открытые источники</h3><p>Вакансии, сайты, реестры и отраслевые каталоги.</p></div>
            <div><span>02</span><h3>Сигналы продаж</h3><p>Признаки региональных и полевых команд.</p></div>
            <div><span>03</span><h3>AI-приоритет</h3><p>Объяснимый рейтинг от 0 до 100.</p></div>
          </div>
        </section>
      )}
    </main>
  );
}
