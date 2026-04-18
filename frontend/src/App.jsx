import React from 'react';
import MedicalDashboard from './components/MedicalDashboard';

function App() {
  return (
    <div className="min-h-screen relative overflow-hidden bg-slate-950 font-sans text-slate-100">
      {/* Background Orbs */}
      <div className="bg-blob bg-medical-600/20 w-[600px] h-[600px] top-[-100px] left-[-200px]" />
      <div className="bg-blob bg-blue-600/20 w-[500px] h-[500px] bottom-[-100px] right-[-100px]" style={{ animationDelay: '2s' }} />
      <div className="bg-blob bg-emerald-600/10 w-[400px] h-[400px] top-[40%] left-[30%]" style={{ animationDelay: '5s' }} />
      
      {/* Main Content */}
      <div className="relative z-10">
        <MedicalDashboard />
      </div>
    </div>
  );
}

export default App;
