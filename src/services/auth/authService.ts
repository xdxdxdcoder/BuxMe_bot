import type { Employee } from '../../types/scout';
import { apiRequest } from '../api/httpClient';
import { maxBridge } from '../max/maxBridge';

export interface AuthService {
  authenticate(employeeCode: string): Promise<Employee>;
}

class MockAuthService implements AuthService {
  async authenticate(employeeCode: string): Promise<Employee> {
    await new Promise((resolve) => window.setTimeout(resolve, 550));
    const user = maxBridge.getUserForPresentation();
    return {
      id: `employee-${employeeCode.toLowerCase()}`,
      code: employeeCode,
      displayName: user?.first_name ? `${user.first_name}${user.last_name ? ` ${user.last_name}` : ''}` : 'Менеджер Buxme',
      maxUserId: user?.id,
      avatarUrl: user?.photo_url ?? undefined,
    };
  }
}

class HttpAuthService implements AuthService {
  authenticate(employeeCode: string): Promise<Employee> {
    return apiRequest<Employee>('/api/auth/max', {
      method: 'POST',
      body: JSON.stringify({ employeeCode, initData: maxBridge.getInitData() }),
    });
  }
}

export const authService: AuthService =
  import.meta.env.VITE_APP_MODE === 'live' ? new HttpAuthService() : new MockAuthService();
