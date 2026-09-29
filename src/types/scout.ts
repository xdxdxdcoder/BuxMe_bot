export type ScoreLevel = 'high' | 'medium' | 'low';
export type CompanyStatus = 'new' | 'in_progress' | 'contacted' | 'promising' | 'not_fit';

export interface AIScore {
  value: number;
  level: ScoreLevel;
  label: string;
  explanation: string;
}

export interface CompanySource {
  id: string;
  title: string;
  category: 'vacancy' | 'website' | 'registry' | 'catalog';
  url?: string;
  checkedAt: string;
}

export interface Company {
  id: string;
  entityType?: 'legal_entity' | 'sole_proprietor';
  name: string;
  region: string;
  city?: string;
  inn: string;
  phone: string;
  email: string;
  website: string;
  description: string;
  score: AIScore;
  signals: string[];
  reasons: string[];
  sources: CompanySource[];
  status: CompanyStatus;
  employeesRange: string;
  employeesYear?: number | null;
  industry: string;
}

export interface SearchRequest {
  region: string;
  limit?: number;
  offset?: number;
}

export interface SearchResponse {
  requestId: string;
  region: string;
  companies: Company[];
  total: number;
  availableTotal: number;
  offset: number;
  hasMore: boolean;
  searchedAt: string;
  mode: 'mock' | 'live' | 'snapshot' | 'registry';
  scoringMode?: 'giga' | 'factual' | 'mock';
  sourceDate?: string | null;
}

export interface Employee {
  id: string;
  code: string;
  displayName: string;
  maxUserId?: number;
  avatarUrl?: string;
}

export interface ContactResult {
  reachedDecisionMaker: 'yes' | 'no' | 'unknown';
  hasFieldTeam: 'yes' | 'no' | 'unknown';
  automationInterest: 'yes' | 'no' | 'unknown';
  notes?: string;
}

export interface ScoreRecalculation {
  previousScore: number;
  newScore: number;
  delta: number;
  explanation: string;
}

export interface GeneratedContent {
  title: string;
  body: string;
}
