import type { MaxInitDataUnsafe, MaxUser } from '../../types/max';

export const maxBridge = {
  isAvailable(): boolean {
    // CDN-скрипт создаёт объект и в обычном браузере, но без подписанного initData.
    // Проверка строки не даёт отправлять нативные события в отсутствующий transport.
    return Boolean(window.WebApp?.initData);
  },

  getInitData(): string {
    return window.WebApp?.initData ?? '';
  },

  getUnsafeLaunchData(): MaxInitDataUnsafe | null {
    return window.WebApp?.initDataUnsafe ?? null;
  },

  getUserForPresentation(): MaxUser | null {
    // Эти данные подходят только для UI. Доверять им можно лишь после серверной проверки initData.
    return window.WebApp?.initDataUnsafe?.user ?? null;
  },

  setBackHandler(handler: (() => void) | null): () => void {
    const backButton = this.isAvailable() ? window.WebApp?.BackButton : undefined;
    if (!backButton) return () => undefined;

    if (!handler) {
      backButton.hide();
      return () => undefined;
    }

    backButton.show();
    backButton.onClick(handler);
    return () => {
      backButton.offClick(handler);
      backButton.hide();
    };
  },

  haptic(style: 'soft' | 'light' | 'medium' = 'light'): void {
    try {
      if (this.isAvailable()) window.WebApp?.HapticFeedback?.impactOccurred(style);
    } catch {
      // В браузере и старых клиентах MAX haptic недоступен — это не ошибка сценария.
    }
  },

  notify(type: 'error' | 'success' | 'warning'): void {
    try {
      if (this.isAvailable()) window.WebApp?.HapticFeedback?.notificationOccurred?.(type);
    } catch {
      // Graceful degradation вне мобильного клиента.
    }
  },

  openExternal(url: string): void {
    if (this.isAvailable()) window.WebApp?.openLink(url);
    else window.open(url, '_blank', 'noopener,noreferrer');
  },
};
