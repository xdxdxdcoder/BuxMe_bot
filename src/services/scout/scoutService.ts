import { MOCK_COMPANIES } from '../../mocks/companies';
import type { SearchRequest, SearchResponse } from '../../types/scout';
import { apiRequest } from '../api/httpClient';

export interface ScoutService {
  searchCompanies(request: SearchRequest): Promise<SearchResponse>;
}

const wait = (ms: number) => new Promise((resolve) => window.setTimeout(resolve, ms));

class MockScoutService implements ScoutService {
  async searchCompanies(request: SearchRequest): Promise<SearchResponse> {
    await wait(2600);
    const normalized = request.region.trim();
    return {
      requestId: crypto.randomUUID(),
      region: normalized,
      companies: MOCK_COMPANIES.slice(request.offset ?? 0, (request.offset ?? 0) + (request.limit ?? 12))
        .map((company) => ({ ...company, region: normalized })),
      total: Math.min(request.limit ?? 12, Math.max(0, MOCK_COMPANIES.length - (request.offset ?? 0))),
      availableTotal: MOCK_COMPANIES.length,
      offset: request.offset ?? 0,
      hasMore: (request.offset ?? 0) + (request.limit ?? 12) < MOCK_COMPANIES.length,
      searchedAt: new Date().toISOString(),
      mode: 'mock',
      scoringMode: 'mock',
    };
  }
}

class HttpScoutService implements ScoutService {
  searchCompanies(request: SearchRequest): Promise<SearchResponse> {
    return apiRequest<SearchResponse>('/api/scout/search', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }
}

export const scoutService: ScoutService =
  (import.meta.env.VITE_RUNTIME_MODE || import.meta.env.VITE_APP_MODE) === 'live'
    ? new HttpScoutService() : new MockScoutService();

export const searchCompanies = (region: string, offset = 0) =>
  scoutService.searchCompanies({ region, limit: 12, offset });
