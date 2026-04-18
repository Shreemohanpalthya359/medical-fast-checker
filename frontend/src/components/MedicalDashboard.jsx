import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  ShieldCheck, ShieldAlert, FileText, UploadCloud, CheckCircle2, 
  XCircle, HelpCircle, Loader2, Mic, MicOff, Volume2, 
  History, Download, Image as ImageIcon, Search, 
  ArrowRight, Info, ExternalLink, Menu, X, LogOut,
  Database, Activity, Zap, BarChart2, Layers
} from 'lucide-react';
import { 
  uploadDocument, factCheckClaim, analyzeImage, 
  getHistory, downloadReport, logout,
  batchFactCheck, getStats, getKbStatus
} from '../api';

const MedicalDashboard = () => {
  const [activeTab, setActiveTab] = useState('single'); // single, batch, kb, analytics
  const [claim, setClaim] = useState('');
  const [batchClaims, setBatchClaims] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [batchResults, setBatchResults] = useState([]);
  const [history, setHistory] = useState([]);
  const [stats, setStats] = useState(null);
  const [kbStatus, setKbStatus] = useState(null);
  
  const [showHistory, setShowHistory] = useState(false);
  const [isListening, setIsListening] = useState(false);
  const [uploadStatus, setUploadStatus] = useState({ type: '', message: '' });
  const [activeAnalysisType, setActiveAnalysisType] = useState('text'); // text or image
  const [selectedImage, setSelectedImage] = useState(null);
  const [imagePreview, setImagePreview] = useState(null);

  const recognitionRef = useRef(null);

  useEffect(() => {
    fetchHistory();
    fetchStatsAndKb();
    // Initialize Speech Recognition
    if ('webkitSpeechRecognition' in window) {
      const recognition = new window.webkitSpeechRecognition();
      recognition.continuous = false;
      recognition.interimResults = false;
      recognition.onresult = (event) => {
        const text = event.results[0][0].transcript;
        setClaim(text);
        setIsListening(false);
      };
      recognition.onerror = () => setIsListening(false);
      recognition.onend = () => setIsListening(false);
      recognitionRef.current = recognition;
    }
  }, []);

  const fetchHistory = async () => {
    try {
      const data = await getHistory();
      setHistory(data);
    } catch (err) {
      console.error("Failed to fetch history", err);
    }
  };

  const fetchStatsAndKb = async () => {
    try {
      const [s, k] = await Promise.all([getStats(), getKbStatus()]);
      setStats(s);
      setKbStatus(k);
    } catch (err) {
      console.error("Failed to fetch analytics", err);
    }
  };

  const toggleListening = () => {
    if (isListening) {
      recognitionRef.current?.stop();
    } else {
      setIsListening(true);
      recognitionRef.current?.start();
    }
  };

  const handleSpeech = (text) => {
    const utterance = new SpeechSynthesisUtterance(text);
    window.speechSynthesis.speak(utterance);
  };

  const handleFactCheck = async (e) => {
    e.preventDefault();
    if (!claim.trim()) return;
    
    setLoading(true);
    setResult(null);
    try {
      const data = await factCheckClaim(claim);
      if (data.error) {
        setResult({ status: "ERROR", explanation: data.error });
      } else {
        setResult(data);
        fetchHistory();
        fetchStatsAndKb();
        if (data.explanation) handleSpeech(data.explanation);
      }
    } catch (err) {
      setResult({ status: "ERROR", explanation: "Verification failed." });
    } finally {
      setLoading(false);
    }
  };
  
  const handleBatchVerify = async () => {
    if(!batchClaims.trim()) return;
    setLoading(true);
    try {
      const claimsList = batchClaims.split('\n').filter(c => c.trim().length > 0);
      const data = await batchFactCheck(claimsList);
      setBatchResults(data.results || []);
      fetchHistory();
      fetchStatsAndKb();
    } catch (err) {
      console.error("Batch check failed");
    } finally {
      setLoading(false);
    }
  }

  const handleImageAnalysis = async (e) => {
    e.preventDefault();
    if (!selectedImage) return;

    setLoading(true);
    try {
      const data = await analyzeImage(selectedImage, claim);
      if (data.error) {
        setResult({ status: "ERROR", explanation: data.error });
      } else {
        setResult({
          status: "IMAGE_ANALYSIS",
          explanation: data.analysis,
          confidence: data.confidence,
          symptoms: data.symptoms_detected,
          precautions: data.precautions,
          glossary: data.glossary
        });
      }
    } catch (err) {
      setResult({ status: "ERROR", explanation: "Image analysis failed." });
    } finally {
      setLoading(false);
    }
  };

  const handleFileUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    
    setUploadStatus({ type: 'info', message: 'Indexing...' });
    try {
      await uploadDocument(file);
      setUploadStatus({ type: 'success', message: 'Index updated.' });
      fetchStatsAndKb();
    } catch (err) {
      setUploadStatus({ type: 'error', message: 'Index failed.' });
    }
  };

  const onImageSelect = (e) => {
    const file = e.target.files[0];
    if (file) {
      setSelectedImage(file);
      if (file.type === "application/pdf") {
        setImagePreview("https://upload.wikimedia.org/wikipedia/commons/8/87/PDF_file_icon.svg"); // Placeholder for PDF
      } else {
        setImagePreview(URL.createObjectURL(file));
      }
      setActiveAnalysisType('image');
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'TRUE': return <CheckCircle2 className="w-12 h-12 text-teal-400" />;
      case 'FALSE': return <XCircle className="w-12 h-12 text-rose-400" />;
      case 'UNVERIFIED': return <HelpCircle className="w-12 h-12 text-amber-400" />;
      default: return <ShieldCheck className="w-12 h-12 text-teal-400" />;
    }
  };

  const PipelineVisualizer = ({ result }) => {
    if (!result || !result.pipeline_breakdown) return null;
    return (
      <div className="flex items-center gap-2 text-[10px] uppercase font-black tracking-widest text-slate-500 mt-6 pt-6 border-t border-white/5">
        <span className="flex items-center gap-1"><Database className="w-3 h-3 text-emerald-500"/> {result.pipeline_breakdown.vector_search_ms}ms Vector</span>
        <ArrowRight className="w-3 h-3" />
        <span className="flex items-center gap-1"><Activity className="w-3 h-3 text-blue-500"/> {result.pipeline_breakdown.pubmed_ms}ms PubMed</span>
        <ArrowRight className="w-3 h-3" />
        <span className="flex items-center gap-1"><Zap className="w-3 h-3 text-amber-500"/> {result.pipeline_breakdown.llm_synthesis_ms}ms LLM ({result.model_used})</span>
        <div className="flex-1"></div>
        <span className="text-teal-400 font-bold">TOTAL: {result.processing_time_ms}ms</span>
      </div>
    );
  };

  return (
    <div className="flex h-screen bg-slate-950 text-slate-100 overflow-hidden font-sans">
      
      {/* Sidebar Navigation & History */}
      <AnimatePresence>
        {showHistory && (
          <motion.aside 
            initial={{ x: -300, opacity: 0 }}
            animate={{ x: 0, opacity: 1 }}
            exit={{ x: -300, opacity: 0 }}
            className="w-80 glass-panel border-r border-white/5 h-full z-50 flex flex-col absolute md:relative"
          >
            <div className="p-6 border-b border-white/5 flex items-center justify-between">
              <h1 className="text-xl font-bold medical-gradient-text tracking-tight flex items-center gap-2">
                <ShieldCheck className="w-6 h-6 text-teal-400" /> Aegis QA
              </h1>
              <button onClick={() => setShowHistory(false)} className="md:hidden">
                <X className="w-5 h-5 text-slate-400" />
              </button>
            </div>

            <nav className="p-4 space-y-2 border-b border-white/5">
              <button onClick={() => setActiveTab('single')} className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-bold transition-all ${activeTab === 'single' ? 'bg-teal-500/20 text-teal-400' : 'hover:bg-white/5 text-slate-400'}`}>
                <Search className="w-4 h-4" /> Single Verification
              </button>
              <button onClick={() => setActiveTab('batch')} className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-bold transition-all ${activeTab === 'batch' ? 'bg-teal-500/20 text-teal-400' : 'hover:bg-white/5 text-slate-400'}`}>
                <Layers className="w-4 h-4" /> Batch Processing
              </button>
              <button onClick={() => setActiveTab('kb')} className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-bold transition-all ${activeTab === 'kb' ? 'bg-teal-500/20 text-teal-400' : 'hover:bg-white/5 text-slate-400'}`}>
                <Database className="w-4 h-4" /> Knowledge Base
              </button>
              <button onClick={() => setActiveTab('analytics')} className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-bold transition-all ${activeTab === 'analytics' ? 'bg-teal-500/20 text-teal-400' : 'hover:bg-white/5 text-slate-400'}`}>
                <BarChart2 className="w-4 h-4" /> Analytics
              </button>
            </nav>
            
            <div className="p-6 flex-1 overflow-y-auto">
              <h3 className="text-xs font-black uppercase tracking-widest text-slate-500 mb-4 flex items-center gap-2">
                <History className="w-4 h-4" /> Recent History
              </h3>
              <div className="space-y-3">
                {history.slice(0,5).map((item) => (
                  <div key={item.id} className="p-3 bg-white/5 rounded-xl text-sm hover:border-teal-500/30 cursor-pointer border border-transparent"
                    onClick={() => { setClaim(item.claim); setActiveTab('single'); setShowHistory(false); }}>
                    <p className="font-medium line-clamp-2 mb-2 text-slate-300 text-xs">{item.claim}</p>
                    <div className="flex items-center justify-between">
                      <span className={`text-[9px] font-bold px-2 py-0.5 rounded-full ${item.verdict === 'TRUE' ? 'bg-teal-500/20 text-teal-400' : item.verdict === 'FALSE' ? 'bg-rose-500/20 text-rose-400' : 'bg-amber-500/20 text-amber-400'}`}>{item.verdict}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
            
            <div className="p-6 border-t border-white/5">
              <button onClick={() => { logout(); window.location.reload(); }} className="w-full flex items-center justify-center gap-2 text-slate-400 hover:text-rose-400 transition-colors text-sm font-bold">
                <LogOut className="w-4 h-4" /> Sign Out
              </button>
            </div>
          </motion.aside>
        )}
      </AnimatePresence>

      {/* Main Content */}
      <main className="flex-1 flex flex-col relative overflow-y-auto">
        <div className="bg-blob bg-teal-500/5 top-[10%] left-[20%] animate-blob" />
        <div className="bg-blob bg-blue-500/5 bottom-[20%] right-[10%] animate-blob animation-delay-2000" />

        <header className="p-6 flex items-center gap-4 sticky top-0 z-40 bg-slate-950/80 backdrop-blur-xl border-b border-white/5">
          {!showHistory && (
            <button onClick={() => setShowHistory(true)} className="p-3 glass-panel rounded-xl hover:bg-white/10 transition-colors">
              <Menu className="w-5 h-5" />
            </button>
          )}
          <div>
            <h2 className="text-xl font-bold">Automated Medical Verification</h2>
            <p className="text-[10px] font-black uppercase tracking-widest text-teal-400">LLM & Vector Search Pipeline</p>
          </div>
        </header>

        <div className="max-w-5xl mx-auto w-full p-8 z-10">
          
          {/* TAB: SINGLE CHECK */}
          {activeTab === 'single' && (
            <motion.div initial={{opacity:0, y:20}} animate={{opacity:1, y:0}} className="space-y-8">
              <div className="space-y-6">
                <div className="flex gap-4">
                  <button onClick={() => setActiveAnalysisType('text')} className={`px-6 py-2 rounded-full text-sm font-bold transition-all ${activeAnalysisType === 'text' ? 'bg-teal-500 text-white shadow-lg' : 'glass-panel text-slate-400'}`}>Text</button>
                  <button onClick={() => setActiveAnalysisType('image')} className={`px-6 py-2 rounded-full text-sm font-bold transition-all ${activeAnalysisType === 'image' ? 'bg-blue-600 text-white shadow-lg' : 'glass-panel text-slate-400'}`}>Image/Report</button>
                </div>
                <form onSubmit={activeAnalysisType === 'text' ? handleFactCheck : handleImageAnalysis} className="relative">
                  <div className="absolute -inset-1 bg-gradient-to-r from-teal-500 to-blue-600 rounded-[2.5rem] blur opacity-20"></div>
                  <div className="relative glass-panel rounded-[2.5rem] p-3 flex items-center gap-2">
                    {activeAnalysisType === 'image' && (
                      <label className="ml-2 p-3 glass-panel rounded-2xl hover:bg-white/10 cursor-pointer relative overflow-hidden">
                        {imagePreview ? <img src={imagePreview} className="w-8 h-8 object-cover rounded-md" /> : <ImageIcon className="w-5 h-5 text-blue-400" title="Upload Image or PDF Report" />}
                        <input type="file" className="hidden" onChange={onImageSelect} accept="image/*,.pdf" />
                      </label>
                    )}
                    <input type="text" value={claim} onChange={(e) => setClaim(e.target.value)} placeholder="Enter medical claim to verify..." className="flex-1 bg-transparent px-6 py-4 outline-none text-lg text-white" disabled={loading} />
                    <button type="button" onClick={toggleListening} className={`p-4 rounded-full ${isListening ? 'bg-rose-500/20 text-rose-400 animate-pulse' : 'hover:bg-white/10 text-slate-400'}`}>
                      {isListening ? <MicOff className="w-5 h-5" /> : <Mic className="w-5 h-5" />}
                    </button>
                    <button type="submit" disabled={loading} className="btn-primary p-4 rounded-full w-14 h-14">
                      {loading ? <Loader2 className="w-5 h-5 animate-spin" /> : <Search className="w-5 h-5" />}
                    </button>
                  </div>
                </form>
              </div>

              <AnimatePresence mode="wait">
                {result && !loading && (
                  <motion.div initial={{opacity:0}} animate={{opacity:1}} exit={{opacity:0}} className="grid lg:grid-cols-3 gap-8">
                    <div className={`col-span-2 glass-panel p-10 rounded-[3rem] border-t-2 ${result.status === 'TRUE' ? 'border-teal-500 bg-teal-950/20' : result.status === 'FALSE' ? 'border-rose-500 bg-rose-950/20' : 'border-amber-500 bg-amber-950/20'}`}>
                      <div className="flex gap-8">
                        <div className="text-center">
                          {getStatusIcon(result.status)}
                          <div className="text-3xl font-black mt-4">{result.confidence || 0}%</div>
                          <div className="text-[10px] font-black uppercase tracking-widest text-slate-500 mt-1">Confidence</div>
                        </div>
                        <div className="flex-1">
                          <h2 className={`text-sm font-black uppercase tracking-widest ${result.status === 'TRUE' ? 'text-teal-400' : result.status === 'FALSE' ? 'text-rose-400' : 'text-amber-400'}`}>{result.status}</h2>
                          <p className="text-xl font-bold mt-2 leading-relaxed">{result.explanation}</p>
                          <PipelineVisualizer result={result} />

                          {result.symptoms && result.symptoms.length > 0 && (
                            <div className="mt-6">
                              <h4 className="text-xs font-black uppercase text-rose-400 tracking-widest mb-2">Detected Symptoms/Findings</h4>
                              <div className="flex flex-wrap gap-2">
                                {result.symptoms.map((s, i) => <span key={i} className="text-xs font-bold px-3 py-1 rounded-lg bg-rose-500/10 text-rose-400 border border-rose-500/20">{s}</span>)}
                              </div>
                            </div>
                          )}

                          {result.precautions && result.precautions.length > 0 && (
                            <div className="mt-6">
                              <h4 className="text-xs font-black uppercase text-amber-400 tracking-widest mb-2">Precautions & Next Steps</h4>
                              <ul className="space-y-2">
                                {result.precautions.map((p, i) => <li key={i} className="text-sm font-medium text-slate-300 flex items-start gap-2"><div className="w-1.5 h-1.5 rounded-full bg-amber-400 mt-1.5"></div>{p}</li>)}
                              </ul>
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                    <div className="space-y-6">
                      {result.detailed_sources && (
                        <div className="glass-panel p-6 rounded-3xl">
                           <h3 className="text-xs font-black uppercase text-blue-400 mb-4">Vector Matches ({result.vector_hits || 0})</h3>
                           <div className="space-y-3 max-h-[300px] overflow-y-auto pr-2">
                             {result.detailed_sources.map((s,i) => (
                               <div key={i} className="p-3 bg-white/5 rounded-xl text-xs relative group">
                                 <div className="absolute top-2 right-2 px-2 py-1 bg-slate-900 rounded text-[9px] font-bold text-teal-400">{Math.round(s.similarity * 100)}% Match</div>
                                 <div className="font-bold text-slate-300 pr-12">{s.topic?.toUpperCase() || 'KB'}</div>
                                 <p className="text-slate-500 mt-1 line-clamp-3">{s.snippet}</p>
                               </div>
                             ))}
                           </div>
                        </div>
                      )}
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </motion.div>
          )}

          {/* TAB: BATCH CHECK */}
          {activeTab === 'batch' && (
             <motion.div initial={{opacity:0, y:20}} animate={{opacity:1, y:0}} className="space-y-8">
               <div className="glass-panel p-8 rounded-3xl">
                 <h2 className="text-xl font-bold flex items-center gap-3 mb-6"><Layers className="text-teal-400 w-6 h-6"/> Batch Processing</h2>
                 <p className="text-slate-400 text-sm mb-4">Paste multiple medical claims (one per line) to verify them automatically.</p>
                 <textarea 
                   className="w-full h-48 bg-slate-900 border border-white/10 rounded-2xl p-4 text-white placeholder-slate-600 focus:outline-none focus:border-teal-500/50"
                   placeholder="Aspirin is used to treat arthritis..&#10;mRNA vaccines alter DNA...&#10;Metformin lowers blood sugar..."
                   value={batchClaims}
                   onChange={e => setBatchClaims(e.target.value)}
                 />
                 <button onClick={handleBatchVerify} disabled={loading || !batchClaims.trim()} className="mt-6 btn-primary">
                    {loading ? <><Loader2 className="w-5 h-5 animate-spin" /> Processing List...</> : <><Search className="w-5 h-5"/> Verify All Claims</>}
                 </button>
               </div>

               {batchResults.length > 0 && (
                 <div className="glass-panel p-8 rounded-3xl overflow-hidden">
                   <h3 className="text-lg font-bold mb-6">Batch Results</h3>
                   <div className="overflow-x-auto">
                     <table className="w-full text-sm text-left">
                       <thead className="text-xs uppercase bg-slate-900/50 text-slate-500">
                         <tr>
                           <th className="px-4 py-3 rounded-tl-xl w-1/2">Claim</th>
                           <th className="px-4 py-3 text-center">Verdict</th>
                           <th className="px-4 py-3 text-center">Conf.</th>
                           <th className="px-4 py-3 text-right">Time</th>
                         </tr>
                       </thead>
                       <tbody className="divide-y divide-white/5">
                         {batchResults.map((r, i) => (
                           <tr key={i} className="hover:bg-white/5 transition-colors group">
                             <td className="px-4 py-4 font-medium text-slate-300" title={r.explanation}>{r.claim}</td>
                             <td className="px-4 py-4 text-center">
                               <span className={`text-[10px] font-bold px-2 py-1 rounded-full ${r.status === 'TRUE' ? 'bg-teal-500/20 text-teal-400' : r.status === 'FALSE' ? 'bg-rose-500/20 text-rose-400' : 'bg-amber-500/20 text-amber-400'}`}>{r.status || 'ERROR'}</span>
                             </td>
                             <td className="px-4 py-4 text-center font-bold text-slate-300">{r.confidence || 0}%</td>
                             <td className="px-4 py-4 text-right text-slate-500 text-xs">{r.processing_time_ms}ms</td>
                           </tr>
                         ))}
                       </tbody>
                     </table>
                   </div>
                 </div>
               )}
             </motion.div>
          )}

          {/* TAB: KNOWLEDGE BASE */}
          {activeTab === 'kb' && (
            <motion.div initial={{opacity:0, y:20}} animate={{opacity:1, y:0}} className="space-y-8">
              <div className="grid md:grid-cols-3 gap-6">
                <div className="glass-panel p-6 rounded-3xl text-center">
                  <Database className="w-10 h-10 text-teal-400 mx-auto mb-4" />
                  <div className="text-4xl font-black">{kbStatus?.total_chunks || 0}</div>
                  <div className="text-[10px] font-black uppercase tracking-widest text-slate-500 mt-2">Vectorized Chunks</div>
                </div>
                <div className="glass-panel p-6 rounded-3xl text-center">
                  <FileText className="w-10 h-10 text-blue-400 mx-auto mb-4" />
                  <div className="text-4xl font-black">{kbStatus?.total_documents || 0}</div>
                  <div className="text-[10px] font-black uppercase tracking-widest text-slate-500 mt-2">Source Documents</div>
                </div>
                <div className="glass-panel p-6 rounded-3xl relative overflow-hidden group">
                   <div className="absolute inset-0 bg-gradient-to-r from-teal-500 to-emerald-500 opacity-10 group-hover:opacity-20 transition-opacity"></div>
                   <div className="relative z-10 flex flex-col items-center justify-center h-full">
                     <UploadCloud className="w-8 h-8 text-white mb-4" />
                     <h3 className="font-bold mb-2">Upload Medical PDF</h3>
                     <label className="bg-white/10 hover:bg-white/20 transition-colors px-4 py-2 rounded-full text-sm font-bold cursor-pointer">
                       Select File
                       <input type="file" className="hidden" accept=".pdf" onChange={handleFileUpload} />
                     </label>
                     {uploadStatus.message && <p className="text-xs text-teal-400 mt-3 font-bold">{uploadStatus.message}</p>}
                   </div>
                </div>
              </div>

              <div className="glass-panel p-8 rounded-3xl">
                <h3 className="font-bold text-lg mb-6">Topic Distribution</h3>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  {kbStatus?.topic_distribution && Object.entries(kbStatus.topic_distribution).map(([topic, count]) => (
                    <div key={topic} className="bg-white/5 p-4 rounded-2xl flex items-center justify-between">
                      <span className="text-sm font-bold text-slate-300 capitalize">{topic.replace('_',' ')}</span>
                      <span className="bg-teal-500/20 text-teal-400 text-xs font-black px-2 py-1 rounded-full">{count}</span>
                    </div>
                  ))}
                </div>
              </div>
            </motion.div>
          )}

          {/* TAB: ANALYTICS */}
          {activeTab === 'analytics' && (
            <motion.div initial={{opacity:0, y:20}} animate={{opacity:1, y:0}} className="space-y-8">
              <div className="grid grid-cols-2 lg:grid-cols-4 gap-6">
                <div className="glass-panel p-6 rounded-3xl">
                   <div className="text-3xl font-black">{stats?.total_checks || 0}</div>
                   <div className="text-[10px] uppercase font-black tracking-widest text-slate-500 mt-2">Total Queries</div>
                </div>
                <div className="glass-panel p-6 rounded-3xl border-b-4 border-teal-500">
                   <div className="text-3xl font-black text-teal-400">{stats?.true_count || 0}</div>
                   <div className="text-[10px] uppercase font-black tracking-widest text-slate-500 mt-2">Verified True</div>
                </div>
                <div className="glass-panel p-6 rounded-3xl border-b-4 border-rose-500">
                   <div className="text-3xl font-black text-rose-400">{stats?.false_count || 0}</div>
                   <div className="text-[10px] uppercase font-black tracking-widest text-slate-500 mt-2">Debunked False</div>
                </div>
                <div className="glass-panel p-6 rounded-3xl text-center relative overflow-hidden">
                   <div className="absolute inset-0 bg-blue-500/10 mix-blend-overlay"></div>
                   <div className="text-3xl font-black medical-gradient-text relative z-10">{stats?.avg_confidence || 0}%</div>
                   <div className="text-[10px] uppercase font-black tracking-widest text-slate-500 mt-2 relative z-10">Avg Confidence</div>
                </div>
              </div>
            </motion.div>
          )}

        </div>
      </main>
    </div>
  );
};

export default MedicalDashboard;
