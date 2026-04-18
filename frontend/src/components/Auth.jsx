import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { ShieldCheck, Mail, Lock, User, ArrowRight, Loader2 } from 'lucide-react';
import { login, register as registerUser } from '../api';

const Auth = ({ onAuthSuccess }) => {
  const [isLogin, setIsLogin] = useState(true);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [formData, setFormData] = useState({ username: '', password: '' });

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    try {
      if (isLogin) {
        const data = await login(formData.username, formData.password);
        onAuthSuccess(data);
      } else {
        await registerUser(formData.username, formData.password);
        setIsLogin(true);
        setError('Registered successfully! Please login.');
      }
    } catch (err) {
      setError(err.response?.data?.error || 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-6 bg-slate-950 relative overflow-hidden">
      {/* Background blobs */}
      <div className="bg-blob bg-teal-500/10 top-[-10%] left-[-10%] animate-blob" />
      <div className="bg-blob bg-blue-500/10 bottom-[-10%] right-[-10%] animate-blob animation-delay-2000" />

      <motion.div 
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="glass-panel w-full max-w-md p-8 rounded-[2.5rem] relative z-10"
      >
        <div className="flex flex-col items-center mb-10">
          <div className="p-4 bg-teal-500/20 rounded-2xl mb-4 border border-teal-500/30">
            <ShieldCheck className="w-8 h-8 text-teal-400" />
          </div>
          <h2 className="text-3xl font-bold medical-gradient-text">
            {isLogin ? 'Welcome Back' : 'Join Aegis AI'}
          </h2>
          <p className="text-slate-400 mt-2 text-center text-sm">
            {isLogin 
              ? 'Access the next generation of medical intelligence' 
              : 'Create your account to start fact-checking'
            }
          </p>
        </div>

        {error && (
          <div className={`p-4 rounded-xl mb-6 text-sm flex items-center gap-2 ${error.includes('success') ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30' : 'bg-rose-500/20 text-rose-400 border border-rose-500/30'}`}>
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-5">
          <div className="relative group">
            <User className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-500 group-focus-within:text-teal-400 transition-colors" />
            <input 
              type="text" 
              placeholder="Username" 
              required
              className="w-full bg-slate-900/50 border border-white/10 rounded-2xl py-4 pl-12 pr-4 outline-none focus:border-teal-500/50 transition-all text-slate-100 placeholder-slate-500"
              value={formData.username}
              onChange={(e) => setFormData({...formData, username: e.target.value})}
            />
          </div>

          <div className="relative group">
            <Lock className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-500 group-focus-within:text-teal-400 transition-colors" />
            <input 
              type="password" 
              placeholder="Password" 
              required
              className="w-full bg-slate-900/50 border border-white/10 rounded-2xl py-4 pl-12 pr-4 outline-none focus:border-teal-500/50 transition-all text-slate-100 placeholder-slate-500"
              value={formData.password}
              onChange={(e) => setFormData({...formData, password: e.target.value})}
            />
          </div>

          <button 
            type="submit" 
            disabled={loading}
            className="btn-primary w-full mt-4"
          >
            {loading ? (
              <Loader2 className="w-5 h-5 animate-spin" />
            ) : (
              <>
                {isLogin ? 'Sign In' : 'Create Account'}
                <ArrowRight className="w-5 h-5" />
              </>
            )}
          </button>
        </form>

        <div className="mt-8 text-center">
          <button 
            onClick={() => setIsLogin(!isLogin)}
            className="text-slate-400 hover:text-teal-400 text-sm font-medium transition-colors"
          >
            {isLogin ? "Don't have an account? Sign Up" : "Already have an account? Sign In"}
          </button>
        </div>
      </motion.div>
    </div>
  );
};

export default Auth;
