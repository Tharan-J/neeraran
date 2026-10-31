import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Shield, GraduationCap, Building2, Wrench, ArrowRight } from 'lucide-react';
import { Logo } from '../components/Logo';
import { useStore, UserRole } from '../store/useStore';

export const LoginPage: React.FC = () => {
  const navigate = useNavigate();
  const { setRole } = useStore();

  const handleSelectRole = (selectedRole: UserRole) => {
    setRole(selectedRole);
    navigate('/app/overview');
  };

  const ROLES_LIST = [
    {
      id: 'admin' as UserRole,
      title: 'Estate Admin',
      desc: 'Full SCADA digital twin, approvals, Gemini accounting & simulation',
      icon: Shield,
      color: 'bg-sky-500 hover:bg-sky-600 text-white',
      iconBg: 'bg-white/20 text-white'
    },
    {
      id: 'student' as UserRole,
      title: 'Student Resident',
      desc: 'Hostel A water awareness, IS 1172 targets, and CPGRAMS grievances',
      icon: GraduationCap,
      color: 'glass-panel hover:bg-white text-ink-900 dark:text-mist border border-emerald-200 dark:border-emerald-800/30',
      iconBg: 'bg-emerald-100 dark:bg-emerald-950/40 text-emerald-600 dark:text-emerald-400'
    },
    {
      id: 'building_admin' as UserRole,
      title: 'Building Administrator',
      desc: 'Hostel A operations, alert triage, and maintenance dispatching',
      icon: Building2,
      color: 'glass-panel hover:bg-white text-ink-900 dark:text-mist border border-indigo-200 dark:border-indigo-800/30',
      iconBg: 'bg-indigo-100 dark:bg-indigo-950/40 text-indigo-600 dark:text-indigo-400'
    },
    {
      id: 'engineer' as UserRole,
      title: 'Maintenance Engineer',
      desc: 'Assigned work orders, field inspection findings, and verifier closing',
      icon: Wrench,
      color: 'glass-panel hover:bg-white text-ink-900 dark:text-mist border border-amber-200 dark:border-amber-800/30',
      iconBg: 'bg-amber-100 dark:bg-amber-950/40 text-amber-600 dark:text-amber-400'
    }
  ];

  return (
    <div className="min-h-screen bg-mist text-ink-900 flex items-center justify-center p-6">
      <div className="max-w-lg w-full glass-card p-8 shadow-glass border border-white/60 dark:border-white/10 space-y-6 text-center">
        <Logo size="lg" className="justify-center" />
        <div className="space-y-1">
          <h2 className="text-xl font-bold text-ink-900 dark:text-mist">Role-Based Operational Gateway</h2>
          <p className="text-xs text-ink-600 dark:text-sky-300">
            Select one of the 4 operational roles to enter the campus water digital twin
          </p>
        </div>

        <div className="space-y-2.5 pt-2 text-left">
          {ROLES_LIST.map((r) => {
            const Icon = r.icon;
            return (
              <button
                key={r.id}
                onClick={() => handleSelectRole(r.id)}
                className={`w-full p-3.5 rounded-card transition-all flex items-center justify-between group shadow-sm ${r.color}`}
              >
                <div className="flex items-center gap-3">
                  <div className={`w-9 h-9 rounded-pill flex items-center justify-center shrink-0 ${r.iconBg}`}>
                    <Icon className="w-4 h-4" strokeWidth={1.8} />
                  </div>
                  <div>
                    <span className="text-xs font-bold block">{r.title}</span>
                    <span className="text-[11px] opacity-80 block">{r.desc}</span>
                  </div>
                </div>
                <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform shrink-0" strokeWidth={1.5} />
              </button>
            );
          })}
        </div>

        <div className="pt-2 text-[11px] text-ink-500 dark:text-sky-400 font-mono">
          NEERARAN • 4-Role RBAC & Gemini 3.5 Flash-Lite Enabled
        </div>
      </div>
    </div>
  );
};
