import React, { useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate, useLocation } from 'react-router-dom';
import { Navbar } from './components/Navbar';
import { ErrorBoundary } from './components/ErrorBoundary';
import { WaterRiseTransition } from './components/WaterRiseTransition';
import { LandingPage } from './pages/Landing';
import { LoginPage } from './pages/Login';
import { OverviewPage } from './pages/Overview';
import { MapPage } from './pages/MapPage';
import { AgentsPage } from './pages/AgentsPage';
import { ApprovalsPage } from './pages/ApprovalsPage';
import { SimulationPage } from './pages/SimulationPage';
import { EvaluationPage } from './pages/EvaluationPage';
import { ResponsibleAIPage } from './pages/ResponsibleAIPage';
import { SettingsPage } from './pages/SettingsPage';
import { useStore } from './store/useStore';

const AppLayout: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const location = useLocation();
  const isAppRoute = location.pathname.startsWith('/app');

  return (
    <div className="min-h-screen flex flex-col bg-mist text-ink-900 transition-colors duration-300">
      {isAppRoute && <Navbar />}
      <main className="flex-1">
        <WaterRiseTransition>
          <ErrorBoundary>
            {children}
          </ErrorBoundary>
        </WaterRiseTransition>
      </main>
    </div>
  );
};

export const App: React.FC = () => {
  const { setSimState, setSseConnected, toggleDemoSafeMode } = useStore();

  // Global Shift+D keyboard listener for Demo Safe Mode
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.shiftKey && (e.key === 'D' || e.key === 'd')) {
        toggleDemoSafeMode();
        console.log('[NEERARAN] Demo Safe Mode toggled');
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [toggleDemoSafeMode]);

  // Real-time Server-Sent Events (SSE) Stream Listener
  useEffect(() => {
    let evtSource: EventSource | null = null;
    let reconnectTimeout: any = null;

    const connectSSE = () => {
      try {
        evtSource = new EventSource('/api/v1/stream');
        evtSource.onopen = () => {
          setSseConnected(true);
        };
        evtSource.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);
            setSimState(data);
          } catch (err) {}
        };
        evtSource.onerror = () => {
          setSseConnected(false);
          if (evtSource) {
            evtSource.close();
            evtSource = null;
          }
          reconnectTimeout = setTimeout(connectSSE, 3500);
        };
      } catch (err) {
        setSseConnected(false);
        reconnectTimeout = setTimeout(connectSSE, 4000);
      }
    };

    connectSSE();

    return () => {
      if (evtSource) evtSource.close();
      if (reconnectTimeout) clearTimeout(reconnectTimeout);
    };
  }, [setSimState, setSseConnected]);

  return (
    <BrowserRouter>
      <AppLayout>
        <Routes>
          <Route path="/" element={<LandingPage />} />
          <Route path="/login" element={<LoginPage />} />
          <Route path="/app/overview" element={<OverviewPage />} />
          <Route path="/app/map" element={<MapPage />} />
          <Route path="/app/agents" element={<AgentsPage />} />
          <Route path="/app/approvals" element={<ApprovalsPage />} />
          <Route path="/app/simulation" element={<SimulationPage />} />
          <Route path="/app/evaluation" element={<EvaluationPage />} />
          <Route path="/app/responsible-ai" element={<ResponsibleAIPage />} />
          <Route path="/app/settings" element={<SettingsPage />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </AppLayout>
    </BrowserRouter>
  );
};

export default App;
