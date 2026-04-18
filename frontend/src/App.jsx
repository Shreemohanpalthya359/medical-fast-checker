import React, { useState, useEffect } from 'react';
import MedicalDashboard from './components/MedicalDashboard';
import LandingPage from './components/LandingPage';
import Auth from './components/Auth';

function App() {
  const [view, setView] = useState('landing'); // landing, auth, dashboard
  const [user, setUser] = useState(null);

  useEffect(() => {
    const token = localStorage.getItem('token');
    const username = localStorage.getItem('username');
    if (token && username) {
      setUser({ username });
      setView('dashboard');
    }
  }, []);

  const handleAuthSuccess = (data) => {
    setUser({ username: data.username });
    setView('dashboard');
  };

  return (
    <div className="min-h-screen bg-slate-950 font-sans text-slate-100">
      {view === 'landing' && (
        <LandingPage onGetStarted={() => setView('auth')} />
      )}
      
      {view === 'auth' && (
        <Auth onAuthSuccess={handleAuthSuccess} />
      )}

      {view === 'dashboard' && (
        <MedicalDashboard user={user} />
      )}
    </div>
  );
}

export default App;
