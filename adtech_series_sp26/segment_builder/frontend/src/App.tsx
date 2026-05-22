/**
 * Main application component.
 */

import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { BrowserRouter, Route, Routes } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import { AppLayout } from './components/AppLayout';
import { SegmentBuilder } from './features/segment-builder';
import { AllSegmentsPage } from './features/segment-builder/components/AllSegmentsPage';
import { SettingsPage } from './components/SettingsPage';
import './App.css';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
});

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<AppLayout />}>
            <Route index element={<SegmentBuilder />} />
            <Route path="all-segments" element={<AllSegmentsPage />} />
            <Route path="settings" element={<SettingsPage />} />
          </Route>
        </Routes>
        <Toaster position="top-center" />
      </BrowserRouter>
    </QueryClientProvider>
  );
}

export default App;
