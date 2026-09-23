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
      companies: MOCK_COMPANIES.map((company) => ({ ...company, region: normalized })),
      total: MOCK_COMPANIES.length,
      searchedAt: new Date().toISOString(),
      mode: 'mock',
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
  import.meta.env.VITE_APP_MODE === 'live' ? new HttpScoutService() : new MockScoutService();

export const searchCompanies = (region: string) => scoutService.searchCompanies({ region });
