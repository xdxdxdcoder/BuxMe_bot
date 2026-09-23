import { MaxUI } from '@maxhub/max-ui';
import { Navigate, Route, Routes } from 'react-router-dom';
import { LoginPage } from '../features/auth/LoginPage';
import { ScoutPage } from '../features/scout/ScoutPage';
import { CompanyPage } from '../features/company/CompanyPage';
import { ScrollToTop } from '../components/ScrollToTop';
import { AppProvider } from './AppProvider';

export function App() {
  return (
    <MaxUI colorScheme="dark">
      <AppProvider>
        <ScrollToTop />
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/scout" element={<ScoutPage />} />
          <Route path="/company/:companyId" element={<CompanyPage />} />
          <Route path="*" element={<Navigate to="/login" replace />} />
        </Routes>
      </AppProvider>
    </MaxUI>
  );
}
