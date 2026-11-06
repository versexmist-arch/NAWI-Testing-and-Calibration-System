import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import AppLayout from './layouts/AppLayout';
import { ToastProvider } from './components/ui';

import Dashboard from './pages/Dashboard';
import Instruments from './pages/Instruments';
import RegisterInstrument from './pages/RegisterInstrument';
import InstrumentDetail from './pages/InstrumentDetail';
import TestManagement from './pages/TestManagement';
import TestDetail from './pages/TestDetail';
import { EccentricityTest, LinearityTest, RepeatabilityTest } from './pages/TestWorkflows';
import TestHistory from './pages/TestHistory';
import AnalyticsPage from './pages/AnalyticsPage';
import Reports from './pages/Reports';
import AuditHistory from './pages/AuditHistory';
import UsersManagement from './pages/UsersManagement';
import Settings from './pages/Settings';

const App: React.FC = () => {
  return (
    <BrowserRouter>
      <ToastProvider>
        <Routes>
          <Route element={<AppLayout />}>
            <Route path="/" element={<Dashboard />} />

            {/* Instruments */}
            <Route path="/instruments" element={<Instruments />} />
            <Route path="/instruments/register" element={<RegisterInstrument />} />
            <Route path="/instruments/:id" element={<InstrumentDetail />} />
            <Route path="/instruments/:id/edit" element={<RegisterInstrument />} />

            {/* Tests & Workflows */}
            <Route path="/tests" element={<TestManagement />} />
            <Route path="/tests/:id" element={<TestDetail />} />
            <Route path="/tests/eccentricity" element={<EccentricityTest />} />
            <Route path="/tests/linearity" element={<LinearityTest />} />
            <Route path="/tests/repeatability" element={<RepeatabilityTest />} />
            <Route path="/history" element={<TestHistory />} />

            {/* Quality & Reporting */}
            <Route path="/reports" element={<Reports />} />
            <Route path="/analytics" element={<AnalyticsPage />} />
            <Route path="/results" element={<Navigate to="/analytics" replace />} />
            <Route path="/audit" element={<AuditHistory />} />

            {/* Administration */}
            <Route path="/users" element={<UsersManagement />} />
            <Route path="/settings" element={<Settings />} />

            {/* Fallback */}
            <Route path="*" element={<Navigate to="/" replace />} />
          </Route>
        </Routes>
      </ToastProvider>
    </BrowserRouter>
  );
};

export default App;
