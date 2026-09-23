export interface MaxUser {
  id: number;
  first_name: string;
  last_name?: string | null;
  username?: string | null;
  language_code?: string;
  photo_url?: string | null;
}

export interface MaxInitDataUnsafe {
  query_id?: string;
  auth_date?: number;
  hash?: string;
  user?: MaxUser;
  chat?: { id: number; type: 'DIALOG' | 'CHAT' | 'CHANNEL' };
  start_param?: string;
}

export interface MaxBackButton {
  isVisible: boolean;
  show: () => void;
  hide: () => void;
  onClick: (callback: () => void) => void;
  offClick: (callback: () => void) => void;
}

export interface MaxWebApp {
  initData: string;
  initDataUnsafe: MaxInitDataUnsafe;
  platform: 'ios' | 'android' | 'desktop' | 'web' | string;
  version: string;
  deviceName?: string;
  BackButton: MaxBackButton;
  HapticFeedback?: {
    impactOccurred: (style: 'soft' | 'light' | 'medium' | 'heavy' | 'rigid') => void;
    notificationOccurred?: (type: 'error' | 'success' | 'warning') => void;
  };
  getViewportSize?: () => Promise<{ height: string; width: string }>;
  openLink: (url: string) => void;
  shareMaxContent?: (text: string, link?: string) => Promise<unknown>;
  enableClosingConfirmation?: () => void;
  disableClosingConfirmation?: () => void;
}

declare global {
  interface Window {
    WebApp?: MaxWebApp;
  }
}
