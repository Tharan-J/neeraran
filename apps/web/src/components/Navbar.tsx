import React from 'react';
import { NavLink, useLocation, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Moon, Sun, Shield, Eye, Settings, PlayCircle } from 'lucide-react';
import { Logo } from './Logo';
import { StatusPill } from './StatusPill';
import { useStore } from '../store/useStore';

export const Navbar: React.FC = () => {
  const { role, setRole, isNightOps, toggleNightOps, simState } = useStore();
  const location = useLocation();
  const navigate = useNavigate();

  const navLinks = [
    { to: '/app/overview', label: 'Overview' },
    { to: '/app/map', label: 'GIS map' },
    { to: '/app/agents', label: 'Agent pipeline' },
    { to: '/app/approvals', label: 'Approvals' },
    { to: '/app/simulation', label: 'Simulation & scenarios' },
    { to: '/app/evaluation', label: 'Evaluation' },
    { to: '/app/responsible-ai', label: 'Responsible AI' },
  ];

  return (
    <header className="sticky top-4 z-40 px-4 max-w-7xl mx-auto w-full">
      <div className="glass-panel rounded-pill px-5 py-2.5 shadow-glass flex items-center justify-between gap-4">
        {/* Left: Logo & Home Link */}
        <NavLink to="/" className="flex items-center gap-2 group">
          <Logo size="md" />
        </NavLink>

        {/* Center: Sliding Tab Pills */}
        <nav className="hidden lg:flex items-center gap-1 bg-sky-50/50 dark:bg-sky-100/30 p-1 rounded-pill">
          {navLinks.map((link) => {
            const isActive = location.pathname === link.to;
            return (
              <NavLink
                key={link.to}
                to={link.to}
                className={`relative px-4 py-1.5 text-xs font-medium rounded-pill transition-colors ${
                  isActive
                    ? 'text-sky-700 dark:text-mist font-semibold'
                    : 'text-ink-600 dark:text-sky-300 hover:text-ink-900'
                }`}
              >
                {isActive && (
                  <motion.div
                    layoutId="navbar-active-pill"
                    className="absolute inset-0 bg-white dark:bg-sky-500 rounded-pill shadow-sm"
                    transition={{ type: 'spring', bounce: 0.18, duration: 0.4 }}
                  />
                )}
                <span className="relative z-10">{link.label}</span>
              </NavLink>
            );
          })}
        </nav>

        {/* Right: Status, Night Ops & Role Avatar */}
        <div className="flex items-center gap-3">
          <StatusPill />

          {/* Night Ops Dark Toggle */}
          <button
            onClick={toggleNightOps}
            className="p-1.5 rounded-pill text-ink-600 hover:text-ink-900 dark:text-sky-300 hover:bg-sky-100/40 transition-colors"
            title="Toggle Night Ops theme"
          >
            {isNightOps ? <Sun className="w-4 h-4" strokeWidth={1.5} /> : <Moon className="w-4 h-4" strokeWidth={1.5} />}
          </button>

          {/* Role Switcher Pill */}
          <div className="flex items-center gap-2 pl-2 border-l border-sky-100 dark:border-white/10">
            <button
              onClick={() => setRole(role === 'admin' ? 'viewer' : 'admin')}
              className={`flex items-center gap-1.5 px-3 py-1 rounded-pill text-xs font-medium transition-all ${
                role === 'admin'
                  ? 'bg-sky-500 text-white shadow-sm'
                  : 'bg-sky-100 text-sky-700 dark:bg-white/10 dark:text-mist'
              }`}
              title="Click to switch between Estate Admin and Viewer role"
            >
              {role === 'admin' ? (
                <>
                  <Shield className="w-3.5 h-3.5" strokeWidth={1.5} />
                  <span>Estate admin</span>
                </>
              ) : (
                <>
                  <Eye className="w-3.5 h-3.5" strokeWidth={1.5} />
                  <span>Viewer mode</span>
                </>
              )}
            </button>

            <NavLink
              to="/app/settings"
              className="p-1.5 rounded-pill text-ink-600 hover:text-ink-900 dark:text-sky-300 hover:bg-sky-100/40 transition-colors"
              title="Operational Settings"
            >
              <Settings className="w-4 h-4" strokeWidth={1.5} />
            </NavLink>
          </div>
        </div>
      </div>
    </header>
  );
};
