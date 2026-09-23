import { afterEach, describe, expect, it, vi } from 'vitest';
import { maxBridge } from './maxBridge';

describe('maxBridge adapter', () => {
  afterEach(() => {
    delete window.WebApp;
    vi.restoreAllMocks();
  });

  it('degrades gracefully in a regular browser', () => {
    expect(maxBridge.isAvailable()).toBe(false);
    expect(maxBridge.getInitData()).toBe('');
    expect(maxBridge.getUserForPresentation()).toBeNull();
    expect(() => maxBridge.haptic()).not.toThrow();
  });
});
