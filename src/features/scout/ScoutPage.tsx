import { useMemo, useState, type FormEvent } from 'react';
import { ArrowRight, ChevronDown, Clock3, Heart, LogOut, Search, SlidersHorizontal, Sparkles } from 'lucide-react';
import { Navigate, useNavigate } from 'react-router-dom';
import { useAppContext } from '../../app/app-context';
import { BrandMark } from '../../components/BrandMark';
import { LocationAutocomplete } from '../../components/LocationAutocomplete';
import { CompanyCard } from '../company/CompanyCard';
import { SearchProgress } from './SearchProgress';
import { searchCompanies } from '../../services/scout/scoutService';
import { ApiError } from '../../services/api/httpClient';
import { maxBridge } from '../../services/max/maxBridge';
import type { Company } from '../../types/scout';

type SortMode = 'score' | 'name';
const isLiveMode = (import.meta.env.VITE_RUNTIME_MODE || import.meta.env.VITE_APP_MODE) === 'live';

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
  const [loadingMore, setLoadingMore] = useState(false);
  const [loadMoreError, setLoadMoreError] = useState('');
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
    setLoadMoreError('');
    try {
      const response = await searchCompanies(region.trim());
      setSearchResponse(response);
      addRecentRegion(region.trim());
      maxBridge.notify('success');
    } catch (cause) {
      setError(cause instanceof ApiError && cause.status === 503
        ? cause.message
        : 'Поиск временно недоступен. Повторите попытку позже.');
    } finally {
      setLoading(false);
    }
  };

  const openCompany = (company: Company) => navigate(`/company/${company.id}`);

  const loadMore = async () => {
    if (!searchResponse || loadingMore) return;
    setLoadingMore(true);
    setLoadMoreError('');
    try {
      const next = await searchCompanies(searchResponse.region, searchResponse.companies.length);
      const allCompanies = [...searchResponse.companies, ...next.companies];
      setSearchResponse({ ...next, companies: allCompanies, total: allCompanies.length });
    } catch {
      setLoadMoreError('Не удалось загрузить ещё компании. Повторите попытку.');
    } finally {
      setLoadingMore(false);
    }
  };

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
          <h1>Находим дистрибьюторов косметики<br /><em>для проверки</em></h1>
          <p>Показываем компании и ИП с основным ОКВЭД оптовой торговли косметикой и подсказываем, кого проверить в первую очередь.</p>
        </div>
        <form className="search-box" onSubmit={handleSearch} noValidate>
          <label htmlFor="region">Регион или город</label>
          <div className={`search-box__input ${error ? 'input-wrap--error' : ''}`}>
            <Search size={22} />
            <LocationAutocomplete value={region} onChange={(value) => { setRegion(value); setError(''); }} />
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
              <h2>Субъектов МСП в выборке: {searchResponse.availableTotal ?? searchResponse.total}</h2>
              <p>Регион: {searchResponse.region} · {searchResponse.mode === 'live'
                ? 'Актуальные данные Rusprofile, AI-оценка GigaChat'
                : searchResponse.mode === 'registry'
                  ? `Реестр МСП ФНС от ${new Date(searchResponse.sourceDate ?? searchResponse.searchedAt).toLocaleDateString('ru-RU')}, ${searchResponse.scoringMode === 'factual' ? 'расчёт по фактам без AI' : 'индекс с GigaChat'}. Основной ОКВЭД 46.45/46.45.1 — оптовая торговля косметикой и парфюмерией. Ассортимент, каналы продаж и наличие полевой команды требуют проверки.`
                : searchResponse.mode === 'snapshot'
                  ? `Снимок Rusprofile от ${new Date(searchResponse.sourceDate ?? searchResponse.searchedAt).toLocaleDateString('ru-RU')}, AI-оценка GigaChat. Охват: 17 регионов.`
                  : 'Демо-данные'}</p>
            </div>
            {searchResponse.total > 0 ? <div className="results-heading__metric"><Sparkles size={18} /><span>Средний индекс</span><strong>{Math.round(searchResponse.companies.reduce((sum, company) => sum + company.score.value, 0) / searchResponse.total)}/100</strong></div> : null}
          </div>

          <div className="filter-bar">
            <div className="filter-search"><Search size={17} /><input aria-label="Поиск среди результатов" placeholder="Поиск по компаниям" value={query} onChange={(event) => setQuery(event.target.value)} /></div>
            <button className={`filter-button ${onlyFavorites ? 'is-active' : ''}`} type="button" onClick={() => setOnlyFavorites((value) => !value)}><Heart size={16} /> Избранное</button>
            <label className="filter-select"><SlidersHorizontal size={16} /><span>Индекс от</span><select value={minScore} onChange={(event) => setMinScore(Number(event.target.value))}><option value="0">0</option><option value="50">50</option><option value="60">60</option><option value="70">70</option></select><ChevronDown size={15} /></label>
            <label className="filter-select"><span>Сначала</span><select value={sort} onChange={(event) => setSort(event.target.value as SortMode)}><option value="score">сильные</option><option value="name">по названию</option></select><ChevronDown size={15} /></label>
          </div>

          {companies.length ? (
            <div className="company-grid">
              {companies.map((company) => (
                <CompanyCard key={company.id} company={company} favorite={favorites.includes(company.id)} onToggleFavorite={() => { toggleFavorite(company.id); maxBridge.haptic('soft'); }} onOpen={() => openCompany(company)} />
              ))}
            </div>
          ) : (
            <div className="empty-state"><Search size={28} /><h3>Ничего не найдено</h3><p>{searchResponse.total === 0 && searchResponse.mode === 'snapshot'
              ? 'В сохранённом снимке нет компаний для этого региона. Попробуйте Москву или Краснодарский край.'
              : searchResponse.total === 0 && searchResponse.mode === 'registry'
                ? 'В этой выборке реестра МСП нет компаний по указанному городу или региону.'
              : 'Сбросьте фильтры или измените поисковый запрос.'}</p><button className="text-button" type="button" onClick={() => { setQuery(''); setMinScore(0); setOnlyFavorites(false); }}>Сбросить фильтры</button></div>
          )}
          {searchResponse.hasMore ? (
            <div className="load-more">
              <p>Показано {searchResponse.companies.length} из {searchResponse.availableTotal}</p>
              <button className="button button--primary" type="button" disabled={loadingMore} onClick={loadMore}>
                {loadingMore ? 'Загружаем…' : 'Показать ещё'}
              </button>
              {loadMoreError ? <p className="field-error" role="alert">{loadMoreError}</p> : null}
            </div>
          ) : null}
        </section>
      ) : (
        <section className="presearch-state">
          <div className="presearch-state__grid">
            <div><span>01</span><h3>{isLiveMode ? 'Реестр ФНС' : 'Демо-данные'}</h3><p>{isLiveMode ? 'Юридические лица и ИП с профильным ОКВЭД из датированного набора открытых данных.' : 'Синтетические компании для знакомства с интерфейсом.'}</p></div>
            <div><span>02</span><h3>{isLiveMode ? 'Подтверждённые данные' : 'Сценарий продаж'}</h3><p>{isLiveMode ? 'Регион, вид деятельности и сведения о масштабе компании.' : 'Пример признаков для разговора с клиентом.'}</p></div>
            <div><span>03</span><h3>{isLiveMode ? 'AI-приоритет' : 'Демо-рейтинг'}</h3><p>Объяснимый индекс от 0 до 100.</p></div>
          </div>
        </section>
      )}
    </main>
  );
}
