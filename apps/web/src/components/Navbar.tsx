import React, { useState } from 'react';
import { NavLink, useLocation, useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { Moon, Sun, Shield, GraduationCap, Building2, Wrench, ChevronDown, Settings, AlertCircle } from 'lucide-react';
import { Logo } from './Logo';
import { StatusPill } from './StatusPill';
import { useStore, UserRole } from '../store/useStore';

export const Navbar: React.FC = () => {
  const { role, setRole, isNightOps, toggleNightOps } = useStore();
  const location = useLocation();
  const navigate = useNavigate();
  const [roleMenuOpen, setRoleMenuOpen] = useState(false);

  const ROLES_CONFIG: Record<UserRole, { label: string; icon: any; badgeColor: string; roleDesc: string }> = {
    admin: { label: 'Estate Admin', icon: Shield, badgeColor: 'bg-sky-500 text-white', roleDesc: 'Full SCADA & Utility Control' },
    student: { label: 'Student Resident', icon: GraduationCap, badgeColor: 'bg-emerald-500 text-white', roleDesc: 'Hostel A Water Awareness & Grievance Portal' },
    building_admin: { label: 'Building Admin', icon: Building2, badgeColor: 'bg-indigo-500 text-white', roleDesc: 'Hostel A Operations & Inspections' },
    engineer: { label: 'Maintenance Eng', icon: Wrench, badgeColor: 'bg-amber-500 text-white', roleDesc: 'Work Orders & Finding Verification' },
  };

  const getNavLinks = (currentRole: UserRole) => {
    switch (currentRole) {
      case 'student':
        return [
          { to: '/app/overview', label: 'Water Awareness' },
          { to: '/app/map', label: 'Campus Map' },
        ];
      case 'building_admin':
        return [
          { to: '/app/overview', label: 'Building Operations' },
          { to: '/app/map', label: 'Building GIS' },
        ];
      case 'engineer':
        return [
          { to: '/app/overview', label: 'Work Orders' },
          { to: '/app/map', label: 'Network Assets' },
        ];
      case 'admin':
      default:
        return [
          { to: '/app/overview', label: 'Overview' },
          { to: '/app/map', label: 'GIS map' },
          { to: '/app/agents', label: 'Agent pipeline' },
          { to: '/app/approvals', label: 'Approvals' },
          { to: '/app/simulation', label: 'Simulation & scenarios' },
          { to: '/app/evaluation', label: 'Evaluation' },
          { to: '/app/responsible-ai', label: 'Responsible AI' },
        ];
    }
  };

  const navLinks = getNavLinks(role);
  const CurrentRoleIcon = ROLES_CONFIG[role]?.icon || Shield;

  const handleRoleSelect = (newRole: UserRole) => {
    setRole(newRole);
    setRoleMenuOpen(false);
    navigate('/app/overview');
  };

  return (
    <header className="sticky top-4 z-40 px-3 max-w-[1440px] mx-auto w-full">
      <div className="glass-panel rounded-pill px-4 py-2 shadow-glass flex items-center justify-between gap-3">
        {/* Left: Logo & Home Link */}
        <NavLink to="/" className="flex items-center gap-2 group shrink-0">
          <Logo size="md" />
        </NavLink>

        {/* Center: Sliding Tab Pills with clean typography and spacing */}
        <nav className="hidden lg:flex items-center gap-1.5 bg-sky-50/60 dark:bg-sky-100/20 p-1 rounded-pill overflow-x-auto scrollbar-none">
          {navLinks.map((link) => {
            const isActive = location.pathname === link.to;
            return (
              <NavLink
                key={link.to}
                to={link.to}
                className={`relative px-3.5 py-1.5 text-[11.5px] tracking-tight whitespace-nowrap rounded-pill transition-colors shrink-0 ${
                  isActive
                    ? 'text-sky-700 dark:text-mist font-semibold'
                    : 'text-ink-600 dark:text-sky-300 hover:text-ink-900 font-medium'
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

        {/* Right: Status, Night Ops & 4-Role Selector */}
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

          {/* 4-Role Dropdown Selector */}
          <div className="relative flex items-center gap-2 pl-2 border-l border-sky-100 dark:border-white/10">
            <button
              onClick={() => setRoleMenuOpen(!roleMenuOpen)}
              className={`flex items-center gap-1.5 px-3 py-1 rounded-pill text-xs font-medium transition-all ${ROLES_CONFIG[role]?.badgeColor || 'bg-sky-500 text-white'}`}
              title="Click to switch between 4 operational roles"
            >
              <CurrentRoleIcon className="w-3.5 h-3.5" strokeWidth={1.8} />
              <span>{ROLES_CONFIG[role]?.label || 'Estate Admin'}</span>
              <ChevronDown className={`w-3 h-3 transition-transform ${roleMenuOpen ? 'rotate-180' : ''}`} />
            </button>

            {/* Dropdown Menu */}
            <AnimatePresence>
              {roleMenuOpen && (
                <motion.div
                  initial={{ opacity: 0, y: 8, scale: 0.95 }}
                  animate={{ opacity: 1, y: 0, scale: 1 }}
                  exit={{ opacity: 0, y: 8, scale: 0.95 }}
                  className="absolute right-0 top-10 mt-1 w-64 bg-white dark:bg-[#122336] rounded-2xl shadow-xl border border-sky-100 dark:border-white/10 p-2 z-50 space-y-1"
                >
                  <div className="px-3 py-1.5 text-[10px] font-mono uppercase tracking-wider text-ink-400 dark:text-sky-300 font-semibold">
                    Switch Operational Role
                  </div>
                  {(Object.keys(ROLES_CONFIG) as UserRole[]).map((rKey) => {
                    const rInfo = ROLES_CONFIG[rKey];
                    const RIcon = rInfo.icon;
                    const isSelected = role === rKey;
                    return (
                      <button
                        key={rKey}
                        onClick={() => handleRoleSelect(rKey)}
                        className={`w-full flex items-start gap-2.5 px-3 py-2 rounded-xl text-left transition-all ${
                          isSelected
                            ? 'bg-sky-50 dark:bg-white/10 text-sky-700 dark:text-mist font-semibold'
                            : 'hover:bg-sky-50/60 dark:hover:bg-white/5 text-ink-700 dark:text-sky-200'
                        }`}
                      >
                        <RIcon className="w-4 h-4 mt-0.5 shrink-0 text-sky-500" />
                        <div>
                          <div className="text-xs font-medium">{rInfo.label}</div>
                          <div className="text-[10px] text-ink-500 dark:text-sky-400 opacity-80">{rInfo.roleDesc}</div>
                        </div>
                      </button>
                    );
                  })}
                </motion.div>
              )}
            </AnimatePresence>

            {role === 'admin' && (
              <NavLink
                to="/app/settings"
                className="p-1.5 rounded-pill text-ink-600 hover:text-ink-900 dark:text-sky-300 hover:bg-sky-100/40 transition-colors"
                title="Operational Settings"
              >
                <Settings className="w-4 h-4" strokeWidth={1.5} />
              </NavLink>
            )}
          </div>
        </div>
      </div>
    </header>
  );
};
