import { afterEach, describe, expect, it, vi } from 'vitest';
import { searchCompanies } from './scoutService';

describe('searchCompanies', () => {
  afterEach(() => vi.useRealTimers());

  it('returns the stable API contract in mock mode', async () => {
    vi.useFakeTimers();
    const promise = searchCompanies('Краснодарский край');
    await vi.advanceTimersByTimeAsync(2700);
    const response = await promise;

    expect(response.mode).toBe('mock');
    expect(response.region).toBe('Краснодарский край');
    expect(response.total).toBe(response.companies.length);
    expect(response.companies[0].score.value).toBeGreaterThan(0);
  });
});
