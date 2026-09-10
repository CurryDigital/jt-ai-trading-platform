import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter, Routes, Route, Navigate, useParams } from 'react-router-dom'
import './index.css'
import App from './App.jsx'
import DbOutageBanner from './components/DbOutageBanner.jsx'

// Redirect /:mode to /:mode/command
function ModeRedirect() {
  const { mode } = useParams();
  return <Navigate to={`/${mode}/command`} replace />;
}

// Wrapper to handle routing with mode/tab params
function AppWrapper() {
  return (
    <Routes>
      <Route path="/:mode/:tab/*" element={<App />} />
      <Route path="/:mode" element={<ModeRedirect />} />
      <Route path="/" element={<Navigate to="/sim/command" replace />} />
    </Routes>
  );
}

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <BrowserRouter>
      <AppWrapper />
      <DbOutageBanner />
    </BrowserRouter>
  </StrictMode>,
)
