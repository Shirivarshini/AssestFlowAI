import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom';
import { AppShell } from './components/layout/AppShell';
import { AssetDetailPage } from './pages/AssetDetail';
import { DashboardPage } from './pages/Dashboard';
import { EventsPage } from './pages/Events';
import { FinancingPage } from './pages/Financing';
import { ReconciliationPage } from './pages/Reconciliation';
import { AlertsPage } from './pages/Alerts';
import { AuditPage } from './pages/Audit';
import { SimulatorPage } from './pages/Simulator';

function App() {
  return (
    <BrowserRouter>
      <AppShell>
        <Routes>
          <Route path="/" element={<DashboardPage />} />
          <Route path="/dashboard" element={<DashboardPage />} />
          <Route path="/assets/:assetId" element={<AssetDetailPage />} />
          <Route path="/assets/:assetId/financing" element={<FinancingPage />} />
          <Route path="/reconciliation" element={<ReconciliationPage />} />
          <Route path="/events" element={<EventsPage />} />
          <Route path="/alerts" element={<AlertsPage />} />
          <Route path="/audit" element={<AuditPage />} />
          <Route path="/simulator" element={<SimulatorPage />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </AppShell>
    </BrowserRouter>
  );
}

export default App;
