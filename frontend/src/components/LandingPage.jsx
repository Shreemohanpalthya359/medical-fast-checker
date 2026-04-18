import React from 'react';
import { motion } from 'framer-motion';
import { ShieldCheck, Zap, Layers, FileText, Mic, Database, ArrowRight, Activity, Search } from 'lucide-react';

const LandingPage = ({ onGetStarted }) => {
  const features = [
    {
      icon: <Layers className="w-6 h-6 text-teal-400" />,
      title: "Automated Batch Checking",
      desc: "Process multiple medical claims simultaneously with high-speed automated verification pipelines."
    },
    {
      icon: <Database className="w-6 h-6 text-blue-400" />,
      title: "Vector Search Engine",
      desc: "Semantically compare claims against a highly curated vector database of medical facts."
    },
    {
      icon: <Zap className="w-6 h-6 text-emerald-400" />,
      title: "LLM Synthesis",
      desc: "Llama 3.1 synthesizes vector hits and live PubMed data to output clinical explanations."
    },
    {
      icon: <Search className="w-6 h-6 text-purple-400" />,
      title: "Fast Insight Retrieval",
      desc: "Live processing time metrics and confidence indexing for instant credibility decisions."
    }
  ];

  return (
    <div className="min-h-screen bg-slate-950 selection:bg-teal-500/30">
      {/* Hero Section */}
      <section className="relative pt-32 pb-20 px-6 overflow-hidden">
        {/* Background Decorations */}
        <div className="bg-blob bg-teal-500/20 top-[-20%] left-[-10%] animate-blob" />
        <div className="bg-blob bg-blue-600/10 bottom-[-10%] right-[-10%] animate-blob animation-delay-2000" />
        
        <div className="max-w-7xl mx-auto text-center relative z-10">
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-full glass-panel mb-8 border-teal-500/20"
          >
            <Zap className="w-4 h-4 text-teal-400 fill-teal-400" />
            <span className="text-sm font-bold text-teal-200">LLM + Vector Search Pipeline</span>
          </motion.div>

          <motion.h1 
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            className="text-5xl md:text-7xl font-black tracking-tighter mb-8 leading-[1.1]"
          >
            Automated Fast Checking <br />
            <span className="medical-gradient-text">of Medical Information.</span>
          </motion.h1>

          <motion.p 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="text-slate-400 text-xl max-w-2xl mx-auto mb-12 font-medium"
          >
            Using Large Language Models and Vector Search to instantaneously debunk, verify, and cross-reference clinical claims at scale.
          </motion.p>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            className="flex flex-col sm:flex-row items-center justify-center gap-6"
          >
            <button 
              onClick={onGetStarted}
              className="btn-primary"
            >
              Get Started for Free
              <ArrowRight className="w-5 h-5" />
            </button>
            <a href="#features" className="text-slate-100 font-bold hover:text-teal-400 transition-colors flex items-center gap-2">
              View Capabilities
              <Activity className="w-5 h-5" />
            </a>
          </motion.div>
        </div>
      </section>

      {/* Grid Features */}
      <section id="features" className="py-24 px-6">
        <div className="max-w-7xl mx-auto">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
            {features.map((f, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.1 }}
                className="glass-card group"
              >
                <div className="p-3 bg-slate-800/50 rounded-2xl w-fit mb-6 group-hover:bg-teal-500/20 transition-colors">
                  {f.icon}
                </div>
                <h3 className="text-xl font-bold mb-4">{f.title}</h3>
                <p className="text-slate-400 font-medium text-sm leading-relaxed">
                  {f.desc}
                </p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Trust Quote */}
      <section className="py-20 bg-slate-900/40 relative">
        <div className="max-w-4xl mx-auto text-center px-6">
          <ShieldCheck className="w-12 h-12 text-teal-400 mx-auto mb-8 opacity-50" />
          <h2 className="text-3xl md:text-5xl font-bold italic text-slate-200 tracking-tight leading-snug">
            "Aegis has revolutionized the way we cross-reference clinical datasets with emerging scientific consensus."
          </h2>
          <p className="mt-8 text-slate-500 font-bold uppercase tracking-widest text-sm">— Clinical Research Lead</p>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-12 border-t border-white/5 text-center text-slate-600 font-medium text-sm">
        <p>© 2026 Aegis Medical Intelligence. For research purposes only.</p>
      </footer>
    </div>
  );
};

export default LandingPage;
