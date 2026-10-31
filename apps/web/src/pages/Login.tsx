import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Shield, Eye, ArrowRight } from 'lucide-react';
import { Logo } from '../components/Logo';
import { useStore } from '../store/useStore';

export const LoginPage: React.FC = () => {
  const navigate = useNavigate();
  const { setRole } = useStore();

  const handleSelectRole = (selectedRole: 'admin' | 'viewer') => {
    setRole(selectedRole);
    navigate('/app/overview');
  };

  return (
    <div className="min-h-screen bg-mist text-ink-900 flex items-center justify-center p-6">
      <div className="max-w-md w-full glass-card p-8 shadow-glass border border-white/60 dark:border-white/10 space-y-6 text-center">
        <Logo size="lg" className="justify-center" />
        <div className="space-y-1">
          <h2 className="text-xl font-bold text-ink-900 dark:text-mist">Operational Gateway</h2>
          <p className="text-xs text-ink-600 dark:text-sky-300">
            Select a role to access the campus digital twin control center
          </p>
        </div>

        <div className="space-y-3 pt-2">
          <button
            onClick={() => handleSelectRole('admin')}
            className="w-full p-4 rounded-card bg-sky-500 hover:bg-sky-700 text-white font-medium text-left transition-all shadow-md flex items-center justify-between group"
          >
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-pill bg-white/20 flex items-center justify-center text-white">
                <Shield className="w-5 h-5" strokeWidth={1.5} />
              </div>
              <div>
                <span className="text-sm font-bold block">Enter as Estate Admin</span>
                <span className="text-[11px] text-white/80 block">Full control, approvals, valve actions & scenarios</span>
              </div>
            </div>
            <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" strokeWidth={1.5} />
          </button>

          <button
            onClick={() => handleSelectRole('viewer')}
            className="w-full p-4 rounded-card glass-panel hover:bg-white text-ink-900 dark:text-mist font-medium text-left transition-all flex items-center justify-between group border border-sky-200/50 dark:border-white/10"
          >
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-pill bg-sky-100 dark:bg-white/10 flex items-center justify-center text-sky-700 dark:text-sky-300">
                <Eye className="w-5 h-5" strokeWidth={1.5} />
              </div>
              <div>
                <span className="text-sm font-bold block">Enter as Viewer</span>
                <span className="text-[11px] text-ink-600 dark:text-sky-300 block">Read-only monitoring, Warden & Student lenses</span>
              </div>
            </div>
            <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" strokeWidth={1.5} />
          </button>
        </div>

        <div className="pt-2 text-[11px] text-ink-600 dark:text-sky-300 font-mono">
          Simulated Digital Twin • Campus Scale • 48h Resilience Run
        </div>
      </div>
    </div>
  );
};
