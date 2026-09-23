import { useMemo, useState, type PropsWithChildren } from 'react';
import type { Company, Employee, SearchResponse } from '../types/scout';
import { usePersistentState } from '../hooks/usePersistentState';
import { AppContext } from './app-context';

export function AppProvider({ children }: PropsWithChildren) {
  const [employee, setEmployee] = usePersistentState<Employee | null>('buxme.employee', null);
  const [searchResponse, setSearchResponse] = useState<SearchResponse | null>(null);
  const [favorites, setFavorites] = usePersistentState<string[]>('buxme.favorites', []);
  const [recentRegions, setRecentRegions] = usePersistentState<string[]>('buxme.regions', []);
  const [statusOverrides, setStatusOverrides] = usePersistentState<Record<string, Company['status']>>(
    'buxme.statuses',
    {},
  );

  const value = useMemo(
    () => ({
      employee,
      setEmployee,
      searchResponse,
      setSearchResponse,
      favorites,
      toggleFavorite: (companyId: string) =>
        setFavorites((current) =>
          current.includes(companyId) ? current.filter((id) => id !== companyId) : [...current, companyId],
        ),
      recentRegions,
      addRecentRegion: (region: string) =>
        setRecentRegions((current) => [region, ...current.filter((item) => item !== region)].slice(0, 4)),
      statusOverrides,
      setCompanyStatus: (companyId: string, status: Company['status']) =>
        setStatusOverrides((current) => ({ ...current, [companyId]: status })),
    }),
    [employee, favorites, recentRegions, searchResponse, setEmployee, setFavorites, setRecentRegions, setStatusOverrides, statusOverrides],
  );

  return <AppContext.Provider value={value}>{children}</AppContext.Provider>;
}
