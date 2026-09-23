import type { CompanyStatus } from '../types/scout';

export const STATUS_LABELS: Record<CompanyStatus, string> = {
  new: 'Новая',
  in_progress: 'В работе',
  contacted: 'Связались',
  promising: 'Перспективная',
  not_fit: 'Не подходит',
};

export const formatDate = (value: string) =>
  new Intl.DateTimeFormat('ru-RU', { day: 'numeric', month: 'short' }).format(new Date(value));
