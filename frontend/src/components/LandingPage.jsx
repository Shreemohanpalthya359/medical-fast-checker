import React, { useState, useEffect } from 'react';
import { motion, useScroll, useTransform } from 'framer-motion';
import {
  ShieldCheck, Zap, Layers, FileText, Mic, Database,
  ArrowRight, Activity, Search, CheckCircle2, XCircle,
  BarChart3, Bot, BookOpen, Clock, Star, ChevronDown
} from 'lucide-react';

/* ─── Animated stat counter ─────────────────────────────────── */
const Counter = ({ to, suffix = '', duration = 2000 }) => {
  const [val, setVal] = useState(0);
  useEffect(() => {
    let start = 0;
    const step = Math.ceil(to / (duration / 16));
    const timer = setInterval(() => {
      start += step;
      if (start >= to) { setVal(to); clearInterval(timer); }
      else setVal(start);
    }, 16);
    return () => clearInterval(timer);
  }, [to, duration]);
  return <span>{val.toLocaleString()}{suffix}</span>;
};

const FEATURES = [
  {
    icon: <Database className="w-5 h-5" />,
    color: 'teal',
    tag: 'Vector DB',
    title: 'Semantic Search Engine',
    desc: 'Semantically compare claims against 35+ curated medical facts using all-MiniLM-L6-v2 embeddings.'
  },
  {
    icon: <Bot className="w-5 h-5" />,
    color: 'blue',
    tag: 'LLM',
    title: 'Llama 3.1 Synthesis',
    desc: 'Groq-accelerated inference synthesizes vector hits and live PubMed data into clinical verdicts.'
  },
  {
    icon: <Activity className="w-5 h-5" />,
    color: 'purple',
    tag: 'Live Data',
    title: 'PubMed Integration',
    desc: 'Live NCBI Entrez queries cross-reference every claim against current peer-reviewed research.'
  },
  {
    icon: <Layers className="w-5 h-5" />,
    color: 'emerald',
    tag: 'Batch',
    title: 'Automated Batch Mode',
    desc: 'Submit unlimited medical claims as a list and get parallel verification results instantly.'
  },
  {
    icon: <FileText className="w-5 h-5" />,
    color: 'rose',
    tag: 'Reports',
    title: 'PDF Reports & Export',
    desc: 'Generate downloadable clinical-grade PDF reports for every fact-check, complete with citations.'
  },
  {
    icon: <Mic className="w-5 h-5" />,
    color: 'amber',
    tag: 'Voice',
    title: 'Voice Input',
    desc: 'Speak your medical claim directly — Web Speech API transcribes and sends it for verification.'
  },
];

const VERDICTS = [
  { claim: "Aspirin inhibits COX-1 and COX-2 enzymes", status: 'TRUE', conf: 97 },
  { claim: "mRNA vaccines alter human DNA", status: 'FALSE', conf: 99 },
  { claim: "Vitamin C cures the common cold", status: 'UNVERIFIED', conf: 44 },
];

const colorMap = {
  teal:    { bg: 'bg-teal-500/10',    border: 'border-teal-500/20',    text: 'text-teal-400' },
  blue:    { bg: 'bg-blue-500/10',    border: 'border-blue-500/20',    text: 'text-blue-400' },
  purple:  { bg: 'bg-violet-500/10',  border: 'border-violet-500/20',  text: 'text-violet-400' },
  emerald: { bg: 'bg-emerald-500/10', border: 'border-emerald-500/20', text: 'text-emerald-400' },
  rose:    { bg: 'bg-rose-500/10',    border: 'border-rose-500/20',    text: 'text-rose-400' },
  amber:   { bg: 'bg-amber-500/10',   border: 'border-amber-500/20',   text: 'text-amber-400' },
};

const LandingPage = ({ onGetStarted }) => {
  const [activeVerdict, setActiveVerdict] = useState(0);

  useEffect(() => {
    const t = setInterval(() => setActiveVerdict(v => (v + 1) % VERDICTS.length), 2800);
    return () => clearInterval(t);
  }, []);

  return (
    <div className="min-h-screen bg-[rgb(var(--surface-1))] grid-pattern overflow-x-hidden">

      {/* ── NAVBAR ─────────────────────────────────────────── */}
      <nav className="fixed top-0 inset-x-0 z-50 glass border-b border-white/5">
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-teal-400 to-emerald-500 flex items-center justify-center shadow-lg shadow-teal-500/30">
              <ShieldCheck className="w-4 h-4 text-white" />
            </div>
            <span className="text-base font-bold tracking-tight">Aegis <span className="text-teal-400">AI</span></span>
          </div>
          <div className="hidden md:flex items-center gap-8 text-sm font-medium text-slate-400">
            <a href="#features" className="hover:text-white transition-colors">Features</a>
            <a href="#demo"     className="hover:text-white transition-colors">Live Demo</a>
            <a href="#stats"    className="hover:text-white transition-colors">Stats</a>
          </div>
          <button onClick={onGetStarted} className="btn-primary !px-5 !py-2 !text-xs !rounded-xl">
            Launch App <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>
      </nav>

      {/* ── HERO ───────────────────────────────────────────── */}
      <section className="relative min-h-screen flex flex-col items-center justify-center pt-16 px-6 overflow-hidden">
        {/* blobs */}
        <div className="bg-blob blob-teal top-[-10%] left-[-15%] animate-blob" />
        <div className="bg-blob blob-blue  bottom-[-5%] right-[-15%] animate-blob animation-delay-2000" />
        <div className="bg-blob blob-purple top-[30%] right-[10%] animate-blob animation-delay-4000" />

        <div className="relative z-10 max-w-5xl mx-auto text-center">
          {/* pill badge */}
          <motion.div
            initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }}
            className="inline-flex items-center gap-2 mb-8 px-4 py-1.5 rounded-full glass border border-teal-500/20 text-xs font-semibold text-teal-300"
          >
            <span className="w-1.5 h-1.5 rounded-full bg-teal-400 animate-pulse" />
            Powered by Llama 3.1 + ChromaDB + PubMed
          </motion.div>

          {/* headline */}
          <motion.h1
            initial={{ opacity: 0, y: 30 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }}
            className="text-5xl sm:text-6xl md:text-8xl font-black tracking-tighter leading-[1.0] mb-6"
            style={{ fontFamily: 'Syne, sans-serif' }}
          >
            Medical Claims.<br />
            <span className="grad-teal text-glow">Verified by AI.</span>
          </motion.h1>

          <motion.p
            initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }}
            className="text-slate-400 text-lg md:text-xl max-w-2xl mx-auto mb-10 font-medium leading-relaxed"
          >
            Aegis uses RAG pipelines, vector search, and large language models to 
            <span className="text-slate-200 font-semibold"> instantly verify, debunk or confirm </span>
            any medical claim against curated scientific literature.
          </motion.p>

          {/* CTA row */}
          <motion.div
            initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.3 }}
            className="flex flex-col sm:flex-row items-center justify-center gap-4 mb-20"
          >
            <button onClick={onGetStarted} className="btn-primary text-base px-8 py-4 rounded-2xl">
              Start Fact-Checking Free
              <ArrowRight className="w-5 h-5" />
            </button>
            <a href="#features" className="btn-ghost">
              <ChevronDown className="w-4 h-4" />
              See how it works
            </a>
          </motion.div>

          {/* Animated demo verdicts */}
          <motion.div
            initial={{ opacity: 0, y: 40 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.5 }}
            id="demo"
            className="max-w-xl mx-auto"
          >
            <div className="bento-card scan-container p-0 overflow-hidden">
              {/* search bar mockup */}
              <div className="px-5 pt-5 pb-4 flex items-center gap-3 border-b border-white/5">
                <div className="flex gap-1.5">
                  <div className="w-3 h-3 rounded-full bg-rose-500/60" />
                  <div className="w-3 h-3 rounded-full bg-amber-500/60" />
                  <div className="w-3 h-3 rounded-full bg-emerald-500/60" />
                </div>
                <div className="flex-1 h-8 glass-sm rounded-xl px-3 flex items-center">
                  <Search className="w-3 h-3 text-slate-500 mr-2" />
                  <span className="text-xs text-slate-400 font-mono">aegis.ai/verify</span>
                </div>
              </div>

              {/* rotating verdict */}
              <div className="p-6 min-h-[130px] flex flex-col justify-center">
                {VERDICTS.map((v, i) => (
                  <motion.div
                    key={i}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: activeVerdict === i ? 1 : 0, y: activeVerdict === i ? 0 : -10 }}
                    transition={{ duration: 0.4 }}
                    className={`absolute inset-x-6 ${activeVerdict === i ? 'pointer-events-auto' : 'pointer-events-none'}`}
                  >
                    <p className="text-xs text-slate-500 mb-3 font-mono">Verifying claim →</p>
                    <p className="text-sm font-semibold text-slate-200 mb-4">"{v.claim}"</p>
                    <div className="flex items-center gap-3">
                      <span className={v.status === 'TRUE' ? 'badge-true' : v.status === 'FALSE' ? 'badge-false' : 'badge-unverified'}>
                        {v.status}
                      </span>
                      <div className="flex-1 h-1.5 bg-white/5 rounded-full overflow-hidden">
                        <motion.div
                          initial={{ width: 0 }}
                          animate={{ width: `${v.conf}%` }}
                          transition={{ duration: 1, delay: 0.3 }}
                          className={`h-full rounded-full ${v.status === 'TRUE' ? 'bg-emerald-400' : v.status === 'FALSE' ? 'bg-rose-400' : 'bg-amber-400'}`}
                        />
                      </div>
                      <span className="text-xs font-bold text-slate-400">{v.conf}%</span>
                    </div>
                  </motion.div>
                ))}
                <div className="h-20" /> {/* spacer for absolute positioned items */}
              </div>

              {/* bottom dots */}
              <div className="px-6 pb-4 flex gap-1.5">
                {VERDICTS.map((_, i) => (
                  <button key={i} onClick={() => setActiveVerdict(i)}
                    className={`h-1 rounded-full transition-all duration-300 ${activeVerdict === i ? 'w-6 bg-teal-400' : 'w-1.5 bg-white/20'}`}
                  />
                ))}
              </div>
            </div>
          </motion.div>
        </div>

        {/* scroll indicator */}
        <motion.div
          className="absolute bottom-8 left-1/2 -translate-x-1/2 flex flex-col items-center gap-2 text-slate-600"
          animate={{ y: [0, 8, 0] }} transition={{ repeat: Infinity, duration: 2 }}
        >
          <ChevronDown className="w-5 h-5" />
        </motion.div>
      </section>

      {/* ── STATS BAR ──────────────────────────────────────── */}
      <section id="stats" className="py-16 px-6 border-y border-white/5 glass">
        <div className="max-w-5xl mx-auto grid grid-cols-2 md:grid-cols-4 gap-8">
          {[
            { label: 'Medical Facts Indexed', value: 35,    suffix: '+' },
            { label: 'Accuracy Rate',          value: 97,   suffix: '%' },
            { label: 'Avg Latency',             value: 4,    suffix: 's' },
            { label: 'API Integrations',        value: 3,    suffix: '' },
          ].map((s, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, y: 20 }} whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }} transition={{ delay: i * 0.1 }}
              className="text-center"
            >
              <div className="text-4xl md:text-5xl font-black grad-teal mb-2">
                <Counter to={s.value} suffix={s.suffix} />
              </div>
              <div className="text-xs font-semibold text-slate-500 uppercase tracking-widest">{s.label}</div>
            </motion.div>
          ))}
        </div>
      </section>

      {/* ── FEATURES BENTO ─────────────────────────────────── */}
      <section id="features" className="py-32 px-6">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-20">
            <motion.p
              initial={{ opacity: 0 }} whileInView={{ opacity: 1 }} viewport={{ once: true }}
              className="text-xs font-bold uppercase tracking-widest text-teal-400 mb-4"
            >
              Built for precision
            </motion.p>
            <motion.h2
              initial={{ opacity: 0, y: 20 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }}
              className="text-4xl md:text-6xl font-black tracking-tighter grad-teal mb-6"
              style={{ fontFamily: 'Syne, sans-serif' }}
            >
              Enterprise-Grade<br />Medical AI Stack
            </motion.h2>
            <motion.p
              initial={{ opacity: 0 }} whileInView={{ opacity: 1 }} viewport={{ once: true }} transition={{ delay: 0.2 }}
              className="text-slate-400 max-w-xl mx-auto font-medium"
            >
              A fully automated RAG pipeline from document ingestion to clinical-grade fact-checking.
            </motion.p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
            {FEATURES.map((f, i) => {
              const c = colorMap[f.color];
              return (
                <motion.div
                  key={i}
                  initial={{ opacity: 0, y: 30 }} whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true }} transition={{ delay: i * 0.08 }}
                  className="bento-card group"
                >
                  <div className={`inline-flex items-center gap-2 mb-6 px-3 py-1.5 rounded-xl text-xs font-bold ${c.bg} ${c.border} ${c.text} border`}>
                    {f.icon} {f.tag}
                  </div>
                  <h3 className="text-lg font-bold text-white mb-3 group-hover:text-teal-300 transition-colors">{f.title}</h3>
                  <p className="text-sm text-slate-400 leading-relaxed font-medium">{f.desc}</p>
                  
                  {/* decorative corner accent */}
                  <div className={`absolute top-0 right-0 w-24 h-24 ${c.bg} rounded-bl-[80px] opacity-0 group-hover:opacity-100 transition-opacity duration-500`} />
                </motion.div>
              );
            })}
          </div>
        </div>
      </section>

      {/* ── HOW IT WORKS ───────────────────────────────────── */}
      <section className="py-24 px-6">
        <div className="max-w-5xl mx-auto">
          <div className="text-center mb-16">
            <p className="text-xs font-bold uppercase tracking-widest text-teal-400 mb-3">RAG Pipeline</p>
            <h2 className="text-4xl md:text-5xl font-black tracking-tighter text-white" style={{ fontFamily: 'Syne, sans-serif' }}>
              How it works in <span className="grad-teal">3 steps</span>
            </h2>
          </div>

          <div className="grid md:grid-cols-3 gap-6 relative">
            {/* connecting line */}
            <div className="hidden md:block absolute top-8 left-[calc(16.67%+1rem)] right-[calc(16.67%+1rem)] h-px bg-gradient-to-r from-teal-500/30 via-blue-500/30 to-violet-500/30" />

            {[
              {
                step: '01', icon: <Database className="w-6 h-6" />, color: 'text-teal-400',
                title: 'Vector Search', desc: 'Your claim is embedded and similarity-searched against the curated medical knowledge base.'
              },
              {
                step: '02', icon: <Activity className="w-6 h-6" />, color: 'text-blue-400',
                title: 'PubMed Query', desc: 'Live NCBI Entrez API fetches the latest peer-reviewed research abstracts matching your claim.'
              },
              {
                step: '03', icon: <Bot className="w-6 h-6" />, color: 'text-violet-400',
                title: 'LLM Synthesis', desc: 'Llama 3.1 synthesizes all sources and returns a structured TRUE/FALSE/UNVERIFIED verdict with confidence score.'
              },
            ].map((s, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, y: 20 }} whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }} transition={{ delay: i * 0.15 }}
                className="bento-card text-center relative"
              >
                <div className="text-6xl font-black text-white/5 absolute top-4 right-5 select-none" style={{ fontFamily: 'Syne, sans-serif' }}>{s.step}</div>
                <div className={`w-14 h-14 rounded-2xl glass flex items-center justify-center mx-auto mb-5 ${s.color} ring-1 ring-white/10`}>
                  {s.icon}
                </div>
                <h3 className="font-bold text-white text-lg mb-3">{s.title}</h3>
                <p className="text-slate-400 text-sm leading-relaxed">{s.desc}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* ── TESTIMONIAL / TRUST QUOTE ──────────────────────── */}
      <section className="py-24 px-6 overflow-hidden relative">
        <div className="bg-blob blob-teal top-0 left-1/2 -translate-x-1/2" />
        <div className="max-w-4xl mx-auto text-center relative z-10">
          <div className="flex justify-center gap-1 mb-8">
            {[...Array(5)].map((_, i) => <Star key={i} className="w-5 h-5 fill-amber-400 text-amber-400" />)}
          </div>
          <motion.blockquote
            initial={{ opacity: 0, y: 20 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }}
            className="text-2xl md:text-4xl font-bold text-slate-200 leading-snug tracking-tight mb-10"
            style={{ fontFamily: 'Syne, sans-serif' }}
          >
            "Aegis has transformed the way our team cross-references clinical datasets with emerging scientific consensus — cutting fact-check time from hours to 
            <span className="grad-teal"> under 5 seconds.</span>"
          </motion.blockquote>
          <div className="flex items-center justify-center gap-4">
            <div className="w-10 h-10 rounded-full bg-gradient-to-br from-teal-400 to-blue-500 flex items-center justify-center text-white font-bold">C</div>
            <div className="text-left">
              <p className="font-semibold text-white text-sm">Clinical Research Lead</p>
              <p className="text-slate-500 text-xs">Medical Data Science Institute</p>
            </div>
          </div>
        </div>
      </section>

      {/* ── CTA ────────────────────────────────────────────── */}
      <section className="py-24 px-6">
        <motion.div
          initial={{ opacity: 0, y: 30 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }}
          className="max-w-3xl mx-auto bento-card text-center relative overflow-hidden p-16"
          style={{ background: 'linear-gradient(135deg, rgba(20,184,166,0.06) 0%, rgba(99,102,241,0.04) 100%)' }}
        >
          <div className="absolute inset-0 bg-gradient-to-r from-teal-500/5 to-blue-600/5" />
          <div className="relative z-10">
            <div className="inline-flex items-center gap-2 mb-6 px-3 py-1 rounded-full bg-teal-500/10 border border-teal-500/20 text-teal-300 text-xs font-bold">
              <ShieldCheck className="w-3.5 h-3.5" /> Free to Use
            </div>
            <h2 className="text-4xl md:text-5xl font-black tracking-tighter mb-4 text-white" style={{ fontFamily: 'Syne, sans-serif' }}>
              Ready to verify your<br /><span className="grad-teal">medical claims?</span>
            </h2>
            <p className="text-slate-400 mb-10 font-medium">
              No credit card required. Powered by open-source AI. Start in seconds.
            </p>
            <button onClick={onGetStarted} className="btn-primary text-base px-10 py-4 rounded-2xl">
              Launch Aegis AI Now
              <ArrowRight className="w-5 h-5" />
            </button>
          </div>
        </motion.div>
      </section>

      {/* ── FOOTER ─────────────────────────────────────────── */}
      <footer className="border-t border-white/5 py-10 px-6">
        <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2.5">
            <div className="w-7 h-7 rounded-xl bg-gradient-to-br from-teal-400 to-emerald-500 flex items-center justify-center">
              <ShieldCheck className="w-3.5 h-3.5 text-white" />
            </div>
            <span className="text-sm font-bold">Aegis AI</span>
          </div>
          <p className="text-slate-600 text-sm">© 2026 Aegis Medical Intelligence · For research & educational purposes only.</p>
          <div className="flex items-center gap-2 text-xs text-slate-600">
            <span>Built with</span>
            <span className="text-teal-500 font-semibold">Flask + LangChain + React</span>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default LandingPage;
