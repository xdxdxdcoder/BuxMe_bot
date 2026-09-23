import { createContext, useContext } from 'react';
import type { Company, Employee, SearchResponse } from '../types/scout';

export interface AppContextValue {
  employee: Employee | null;
  setEmployee: (employee: Employee | null) => void;
  searchResponse: SearchResponse | null;
  setSearchResponse: (response: SearchResponse | null) => void;
  favorites: string[];
  toggleFavorite: (companyId: string) => void;
  recentRegions: string[];
  addRecentRegion: (region: string) => void;
  statusOverrides: Record<string, Company['status']>;
  setCompanyStatus: (companyId: string, status: Company['status']) => void;
}

export const AppContext = createContext<AppContextValue | null>(null);

export function useAppContext() {
  const value = useContext(AppContext);
  if (!value) throw new Error('useAppContext must be used inside AppProvider');
  return value;
}
