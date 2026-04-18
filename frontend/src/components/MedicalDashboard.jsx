import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ShieldCheck, ShieldAlert, FileText, UploadCloud, CheckCircle2, XCircle, HelpCircle, Loader2 } from 'lucide-react';
import { uploadDocument, factCheckClaim } from '../api';

const MedicalDashboard = () => {
  const [claim, setClaim] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  
  const [uploading, setUploading] = useState(false);
  const [uploadStatus, setUploadStatus] = useState({ type: '', message: '' });

  const handleFactCheck = async (e) => {
    e.preventDefault();
    if (!claim.trim()) return;
    
    setLoading(true);
    setResult(null);
    try {
      const data = await factCheckClaim(claim);
      setResult(data);
    } catch (err) {
      setResult({
        status: "ERROR",
        explanation: err.response?.data?.error || "An error occurred while verifying the claim."
      });
    } finally {
      setLoading(false);
    }
  };

  const handleFileUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    setUploading(true);
    setUploadStatus({ type: 'info', message: 'Extracting semantic knowledge...' });
    
    try {
      const resp = await uploadDocument(file);
      setUploadStatus({
        type: 'success',
        message: `Successfully learned from ${resp.filename} (${resp.chunks_added} sections indexed).`
      });
    } catch (err) {
      setUploadStatus({
        type: 'error',
        message: err.response?.data?.error || 'Failed to process document.'
      });
    } finally {
      setUploading(false);
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'TRUE': return <CheckCircle2 className="w-12 h-12 text-emerald-400" />;
      case 'FALSE': return <XCircle className="w-12 h-12 text-rose-400" />;
      case 'UNVERIFIED': return <HelpCircle className="w-12 h-12 text-amber-400" />;
      default: return <ShieldAlert className="w-12 h-12 text-slate-400" />;
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'TRUE': return 'from-emerald-900/50 to-emerald-800/20 border-emerald-500/30';
      case 'FALSE': return 'from-rose-900/50 to-rose-800/20 border-rose-500/30';
      case 'UNVERIFIED': return 'from-amber-900/50 to-amber-800/20 border-amber-500/30';
      default: return 'from-slate-800/60 to-slate-900/60 border-slate-700/50';
    }
  };

  return (
    <div className="max-w-6xl mx-auto p-6 pt-12 min-h-screen flex flex-col gap-8">
      
      {/* Header */}
      <header className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="p-3 bg-medical-500/20 rounded-2xl border border-medical-500/30 shadow-[0_0_20px_rgba(20,184,166,0.3)]">
            <ShieldCheck className="w-8 h-8 text-medical-400" />
          </div>
          <div>
            <h1 className="text-2xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-medical-200 to-medical-500 tracking-tight">
              Aegis Medical Intelligence
            </h1>
            <p className="text-slate-400 text-sm font-medium">Enterprise Fact-Checking Engine</p>
          </div>
        </div>

        {/* Upload Knowledge Base Card */}
        <div className="glass-panel px-4 py-2 rounded-2xl flex items-center gap-4 transition-all hover:bg-white/10 relative">
          <FileText className="w-5 h-5 text-medical-300" />
          <div className="text-sm">
            <p className="font-semibold text-slate-200">Knowledge Base</p>
            {uploadStatus.message ? (
              <p className={`text-xs ${uploadStatus.type === 'success' ? 'text-emerald-400' : uploadStatus.type === 'error' ? 'text-rose-400' : 'text-medical-200'}`}>
                {uploadStatus.message}
              </p>
            ) : (
              <p className="text-xs text-slate-400">Upload PDF to Index</p>
            )}
          </div>
          <label className="ml-4 cursor-pointer p-2 bg-medical-500/20 hover:bg-medical-500/40 rounded-xl transition-colors border border-medical-500/30 flex items-center justify-center">
            {uploading ? <Loader2 className="w-5 h-5 text-medical-200 animate-spin" /> : <UploadCloud className="w-5 h-5 text-medical-200" />}
            <input type="file" accept=".pdf" className="hidden" onChange={handleFileUpload} disabled={uploading} />
          </label>
        </div>
      </header>

      <main className="flex-1 flex flex-col items-center mt-10 w-full max-w-4xl mx-auto gap-8">
        
        {/* Search Bar section */}
        <div className="w-full relative z-20">
          <form onSubmit={handleFactCheck} className="relative group">
            <div className="absolute -inset-1 bg-gradient-to-r from-medical-500 to-blue-600 rounded-[2rem] blur opacity-25 group-hover:opacity-40 transition duration-1000 group-hover:duration-200"></div>
            <div className="relative glass-panel rounded-[2rem] p-2 flex items-center border border-white/20">
              <input 
                type="text" 
                value={claim}
                onChange={(e) => setClaim(e.target.value)}
                placeholder="Enter a medical claim to verify (e.g. 'Vitamin C prevents COVID-19')"
                className="w-full bg-transparent text-slate-100 placeholder-slate-400 text-lg px-6 py-4 outline-none font-medium"
                disabled={loading}
              />
              <button 
                type="submit"
                disabled={loading || !claim.trim()}
                className="mr-2 px-8 py-4 bg-gradient-to-r from-medical-600 to-medical-500 hover:from-medical-500 hover:to-medical-400 rounded-full font-bold shadow-lg text-white transition-all transform hover:scale-[1.02] active:scale-95 disabled:opacity-50 disabled:hover:scale-100 flex items-center gap-2"
              >
                {loading ? (
                  <>
                    <Loader2 className="w-5 h-5 animate-spin" />
                    Analyzing
                  </>
                ) : (
                  "Verify"
                )}
              </button>
            </div>
          </form>
        </div>

        {/* Results grid */}
        <AnimatePresence mode="wait">
          {result && (
            <motion.div 
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              className="w-full grid grid-cols-1 md:grid-cols-3 gap-6"
            >
              {/* Primary Verdict Card */}
              <div className={`md:col-span-2 rounded-3xl p-8 border bg-gradient-to-br shadow-2xl ${getStatusColor(result.status)} backdrop-blur-md relative overflow-hidden`}>
                <div className="absolute top-0 right-0 w-64 h-64 bg-white/5 rounded-full blur-3xl -translate-y-1/2 translate-x-1/4"></div>
                
                <div className="flex items-start gap-6 relative z-10">
                  <div className="bg-slate-900/40 p-4 rounded-2xl shadow-inner backdrop-blur-sm border border-white/10">
                    {getStatusIcon(result.status)}
                  </div>
                  <div>
                    <h2 className="text-slate-400 text-sm font-semibold tracking-wider uppercase mb-1">AI Verdict</h2>
                    <div className="flex items-end gap-4 mb-4">
                      <span className="text-4xl font-extrabold tracking-tight text-white shadow-sm">
                        {result.status}
                      </span>
                      {result.confidence !== undefined && (
                        <div className="flex items-center gap-2 mb-1">
                          <div className="h-2 w-24 bg-slate-800 rounded-full overflow-hidden">
                            <motion.div 
                              initial={{ width: 0 }}
                              animate={{ width: `${result.confidence}%` }}
                              transition={{ duration: 1, delay: 0.2 }}
                              className={`h-full ${result.status === 'TRUE' ? 'bg-emerald-400' : result.status === 'FALSE' ? 'bg-rose-400' : 'bg-amber-400'}`}
                            />
                          </div>
                          <span className="text-sm font-bold text-slate-300">{result.confidence}% Confidence</span>
                        </div>
                      )}
                    </div>
                    <p className="text-slate-200 text-lg leading-relaxed font-medium">
                      {result.explanation}
                    </p>
                  </div>
                </div>
              </div>

              {/* Sources / Evidence Card */}
              <div className="glass-panel p-6 rounded-3xl flex flex-col">
                <div className="flex items-center gap-2 mb-6">
                  <FileText className="w-5 h-5 text-medical-300" />
                  <h3 className="font-semibold text-lg">Cited Evidence</h3>
                </div>
                
                {result.documents_referenced && result.documents_referenced.length > 0 ? (
                  <div className="flex-1 flex flex-col gap-3">
                    {result.documents_referenced.map((doc, idx) => (
                      <div key={idx} className="bg-slate-800/40 border border-slate-700/50 p-4 rounded-xl hover:bg-slate-800/60 transition-colors cursor-default">
                        <p className="text-sm font-medium text-slate-300 truncate" title={doc}>📄 {doc}</p>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="flex-1 flex flex-col items-center justify-center text-center p-4 bg-slate-900/30 rounded-2xl border border-slate-800/50">
                    <ShieldAlert className="w-8 h-8 text-slate-500 mb-2 opacity-50" />
                    <p className="text-sm text-slate-400">No specific documents found in knowledge base for this claim.</p>
                  </div>
                )}
                
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </main>
    </div>
  );
};

export default MedicalDashboard;
