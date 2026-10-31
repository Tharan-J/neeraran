import React, { useState } from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { ArrowRight, CheckCircle2, ShieldCheck, AlertCircle, Sparkles, Activity, Layers, Sliders, Check, X } from 'lucide-react';
import { Logo } from '../components/Logo';

export const LandingPage: React.FC = () => {
  const navigate = useNavigate();
  const [activeStep, setActiveStep] = useState(0);
  const [mockApproved, setMockApproved] = useState<boolean | null>(null);

  const steps = [
    { title: 'Monitor', desc: 'Validates 5-minute ticks across 20 campus blocks and storage tanks, separating sensor dropout from physical pipe leaks.' },
    { title: 'Detect', desc: 'Ensemble IsolationForest and night-flow z-score requires >=2 independent signals before raising a leak hypothesis.' },
    { title: 'Localize', desc: 'Zone mass balance and hydraulic pressure gradients rank the top-3 affected pipe segments.' },
    { title: 'Predict', desc: 'Holt-Winters 7-day demand models and 72-hour tank depletion curves project reserve hours with an 80% band.' },
    { title: 'Prioritize', desc: 'Transparent mathematical scoring ranks cases by loss rate, population, vulnerability weight, and urgency.' },
    { title: 'Optimize', desc: 'SciPy linprog schedules pump schedules and valve throttling with a hard guarantee: 0 vulnerable-block violations.' },
    { title: 'Verify & Intervene', desc: 'Verifier confirms evidence citations before dispatching CMMS tickets, while consequential restrictions await human approval.' }
  ];

  return (
    <div className="min-h-screen bg-mist text-ink-900 overflow-x-hidden">
      {/* Top Hero Container with Sky Gradient */}
      <section className="p-4 md:p-6 max-w-7xl mx-auto">
        <div className="relative rounded-[32px] overflow-hidden bg-gradient-to-b from-[#3A8FDA] via-[#6DB1E8] to-[#D9E9FB] dark:from-[#132437] dark:via-[#1A3450] dark:to-[#0B1622] p-6 md:p-12 text-ink-900 dark:text-mist shadow-lg border border-white/40 dark:border-white/10">
          
          {/* Subtle clouds background effect */}
          <div className="absolute inset-0 opacity-20 pointer-events-none bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-white via-transparent to-transparent"></div>

          {/* Nav inside hero */}
          <header className="relative z-10 flex items-center justify-between pb-12">
            <Logo size="md" />
            <div className="hidden md:flex items-center gap-6 text-xs font-medium text-ink-900/80 dark:text-mist/80">
              <a href="#how-it-works" className="hover:text-ink-900 dark:hover:text-white transition-colors">How it works</a>
              <a href="#guardrails" className="hover:text-ink-900 dark:hover:text-white transition-colors">Guardrails</a>
              <a href="#impact" className="hover:text-ink-900 dark:hover:text-white transition-colors">Impact</a>
            </div>
            <button
              onClick={() => navigate('/login')}
              className="px-5 py-2.5 rounded-pill bg-white text-sky-700 dark:bg-sky-500 dark:text-white text-xs font-semibold shadow-sm hover:shadow-md transition-all flex items-center gap-2"
            >
              <span>Open control center</span>
              <ArrowRight className="w-3.5 h-3.5" strokeWidth={1.5} />
            </button>
          </header>

          {/* Hero Content */}
          <div className="relative z-10 max-w-3xl pt-4 pb-16 space-y-6">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-pill bg-white/70 dark:bg-white/10 text-sky-700 dark:text-sky-300 text-xs font-medium border border-white/60 shadow-sm">
              <Sparkles className="w-3 h-3" />
              <span>Campus water, simulated and guarded</span>
            </div>

            <h1 className="text-4xl md:text-6xl font-light tracking-tight leading-[1.15] text-ink-900 dark:text-white">
              Your all-in-one fortress for <br />
              <span className="font-extrabold text-sky-700 dark:text-sky-300 inline-block">
                smarter campus water
              </span>
            </h1>

            <p className="text-base md:text-lg text-ink-600 dark:text-sky-100/90 font-normal max-w-2xl leading-relaxed">
              Spots a leak before the tank drops, forecasts the shortage, ranks the repairs, and waits for a human to say yes.
            </p>

            <div className="flex flex-wrap items-center gap-4 pt-2">
              <button
                onClick={() => navigate('/login')}
                className="px-7 py-3 rounded-btn bg-sky-500 hover:bg-sky-700 text-white font-medium text-sm shadow-md transition-all flex items-center gap-2"
              >
                <span>Open control center</span>
                <ArrowRight className="w-4 h-4" strokeWidth={1.5} />
              </button>
              <a
                href="#replay"
                className="px-6 py-3 rounded-btn glass-panel text-ink-900 dark:text-mist font-medium text-sm hover:bg-white/40 transition-colors"
              >
                Watch the 90-second replay
              </a>
            </div>
          </div>

          {/* Live Miniature Preview Rising out of Hero bottom */}
          <div className="relative mt-8 rounded-card glass-panel border border-white/60 dark:border-white/10 p-5 shadow-2xl overflow-hidden max-w-5xl mx-auto backdrop-blur-md">
            <div className="flex items-center justify-between pb-4 border-b border-white/30 dark:border-white/10 text-xs">
              <div className="flex items-center gap-2">
                <span className="w-2.5 h-2.5 rounded-full bg-coral animate-ping"></span>
                <span className="font-semibold text-ink-900 dark:text-mist">Live twin simulation • Tick 184</span>
              </div>
              <span className="text-ink-600 dark:text-sky-300 font-mono">03:15 UTC • Sathyamangalam Campus</span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-4 gap-4 pt-4">
              <div className="p-3 bg-white/40 dark:bg-white/5 rounded-xl">
                <span className="text-[11px] text-ink-600 dark:text-sky-300 block">Water in reserve</span>
                <span className="text-xl font-bold font-mono text-ink-900 dark:text-mist">2.8 days</span>
                <span className="text-[10px] text-aqua block mt-0.5">80% band [2.4 - 3.2 d]</span>
              </div>
              <div className="p-3 bg-white/40 dark:bg-white/5 rounded-xl">
                <span className="text-[11px] text-ink-600 dark:text-sky-300 block">Active leak candidates</span>
                <span className="text-xl font-bold font-mono text-coral">1 verified</span>
                <span className="text-[10px] text-coral block mt-0.5">Hostel A • 58 L/min fissure</span>
              </div>
              <div className="p-3 bg-white/40 dark:bg-white/5 rounded-xl">
                <span className="text-[11px] text-ink-600 dark:text-sky-300 block">Estimated loss today</span>
                <span className="text-xl font-bold font-mono text-ink-900 dark:text-mist">83.5 kL</span>
                <span className="text-[10px] text-amber block mt-0.5">₹3,507 economic loss</span>
              </div>
              <div className="p-3 bg-white/40 dark:bg-white/5 rounded-xl">
                <span className="text-[11px] text-ink-600 dark:text-sky-300 block">Vulnerable violations</span>
                <span className="text-xl font-bold font-mono text-leaf">0 violations</span>
                <span className="text-[10px] text-leaf block mt-0.5">100% minimum supply met</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Story Section: A leak looks like a normal night */}
      <section className="py-20 px-6 max-w-5xl mx-auto space-y-8">
        <div className="max-w-2xl space-y-3">
          <span className="text-xs font-semibold text-sky-500 uppercase tracking-wider">Hydraulic Grounding</span>
          <h2 className="text-3xl font-light text-ink-900 dark:text-mist">
            A leak looks like a <span className="font-bold text-sky-700 dark:text-sky-300">normal night</span>
          </h2>
          <p className="text-sm text-ink-600 dark:text-sky-300 leading-relaxed">
            At 3:00 AM, normal campus hostel night flow drops to 12 L/min. When a riser cracks, flow stays flat at 65 L/min.
            A traditional dashboard just shows usage; NEERARAN cross-references the downstream pressure drop to prove a physical leak before the tank runs dry.
          </p>
        </div>

        {/* Interactive Story Visual */}
        <div className="p-6 rounded-card glass-card shadow-glass flex flex-col md:flex-row items-center justify-between gap-8">
          <div className="space-y-2">
            <span className="text-xs text-ink-600 dark:text-sky-300 font-mono">Telemetry comparison at 03:00 AM</span>
            <div className="flex items-center gap-4">
              <div>
                <span className="text-xs text-ink-600 dark:text-sky-300 block">Baseline Night Flow</span>
                <span className="text-2xl font-bold font-mono text-ink-900 dark:text-mist">12.0 L/min</span>
              </div>
              <div className="h-8 w-px bg-sky-200 dark:bg-white/10"></div>
              <div>
                <span className="text-xs text-coral block">Observed Meter Reading</span>
                <span className="text-2xl font-bold font-mono text-coral">58.4 L/min</span>
              </div>
            </div>
            <p className="text-xs text-ink-600 dark:text-sky-300 pt-2">
              Corroborating signal: Sub-header pressure collapsed from 2.85 bar down to 2.30 bar.
            </p>
          </div>
          <div className="px-4 py-3 rounded-xl bg-coral/10 border border-coral/30 text-coral text-xs font-medium flex items-center gap-2">
            <span className="w-2.5 h-2.5 rounded-full bg-coral animate-ping"></span>
            <span>Flagged: Confirmed Fissure along PIPE-OHT1-HSTLA</span>
          </div>
        </div>
      </section>

      {/* Pinned 7-Step Operational Loop */}
      <section id="how-it-works" className="py-20 px-6 max-w-6xl mx-auto space-y-12">
        <div className="text-center max-w-2xl mx-auto space-y-3">
          <span className="text-xs font-semibold text-sky-500 uppercase tracking-wider">TCS AI Engineering Loop</span>
          <h2 className="text-3xl font-light text-ink-900 dark:text-mist">
            Seven steps, <span className="font-bold text-sky-700 dark:text-sky-300">one continuous loop</span>
          </h2>
          <p className="text-sm text-ink-600 dark:text-sky-300">
            Autonomous reasoning grounded in verifiable sensor telemetry.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-7 gap-2">
          {steps.map((st, idx) => (
            <button
              key={st.title}
              onClick={() => setActiveStep(idx)}
              className={`p-3.5 rounded-2xl text-left transition-all ${
                activeStep === idx
                  ? 'bg-sky-500 text-white shadow-md'
                  : 'bg-white/60 dark:bg-white/5 text-ink-600 dark:text-sky-300 hover:bg-white'
              }`}
            >
              <span className="text-[10px] font-mono opacity-80 block">0{idx + 1}</span>
              <span className="text-xs font-bold block mt-1">{st.title}</span>
            </button>
          ))}
        </div>

        <div className="p-8 rounded-card glass-card shadow-glass max-w-4xl mx-auto">
          <div className="flex items-start gap-4">
            <div className="w-10 h-10 rounded-pill bg-sky-100 dark:bg-white/10 text-sky-700 dark:text-sky-300 flex items-center justify-center font-bold text-sm shrink-0">
              0{activeStep + 1}
            </div>
            <div className="space-y-2">
              <h3 className="text-lg font-bold text-ink-900 dark:text-mist">{steps[activeStep].title} Agent</h3>
              <p className="text-sm text-ink-600 dark:text-sky-300 leading-relaxed">
                {steps[activeStep].desc}
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Human Control Card */}
      <section id="guardrails" className="py-20 px-6 max-w-5xl mx-auto space-y-8">
        <div className="max-w-xl space-y-3">
          <span className="text-xs font-semibold text-sky-500 uppercase tracking-wider">Human Control & Safety</span>
          <h2 className="text-3xl font-light text-ink-900 dark:text-mist">
            You <span className="font-bold text-sky-700 dark:text-sky-300">stay in charge</span>
          </h2>
          <p className="text-sm text-ink-600 dark:text-sky-300">
            The AI never autonomously imposes supply restrictions on vulnerable blocks.
            All consequential valve operations require explicit Estate Admin approval with full equity impact checks.
          </p>
        </div>

        <div className="p-6 rounded-card glass-card max-w-xl shadow-glass space-y-4 border border-sky-200 dark:border-white/10">
          <div className="flex items-center justify-between text-xs">
            <span className="px-2.5 py-1 rounded-pill bg-amber/15 text-amber font-medium">Pending Estate Admin Approval</span>
            <span className="text-ink-600 dark:text-sky-300 font-mono">APP-HSTL-01</span>
          </div>

          <div className="space-y-1">
            <h4 className="font-bold text-sm text-ink-900 dark:text-mist">Throttle Feeder Valve to 40% on Hostel Block A</h4>
            <p className="text-xs text-ink-600 dark:text-sky-300">
              Action proposed by Optimizer to curb 58 L/min fissure while maintenance crew mobilizes.
            </p>
          </div>

          <div className="p-3 rounded-xl bg-sky-50/70 dark:bg-white/5 text-[11px] space-y-1 text-ink-600 dark:text-sky-300">
            <span className="font-semibold text-sky-700 dark:text-sky-300 block">Equity Impact Check:</span>
            <span>Overhead Tank 1 buffered at 92 kL; guaranteed minimum 85% potable supply held for all 650 hostel residents.</span>
          </div>

          <div className="flex items-center gap-3 pt-2">
            {mockApproved === null ? (
              <>
                <button
                  onClick={() => setMockApproved(true)}
                  className="px-4 py-2 rounded-btn bg-leaf text-white text-xs font-semibold flex items-center gap-1.5 shadow-sm hover:opacity-90"
                >
                  <Check className="w-3.5 h-3.5" />
                  <span>Approve intervention</span>
                </button>
                <button
                  onClick={() => setMockApproved(false)}
                  className="px-4 py-2 rounded-btn bg-coral text-white text-xs font-semibold flex items-center gap-1.5 shadow-sm hover:opacity-90"
                >
                  <X className="w-3.5 h-3.5" />
                  <span>Reject action</span>
                </button>
              </>
            ) : mockApproved ? (
              <div className="text-xs text-leaf font-semibold flex items-center gap-1.5">
                <CheckCircle2 className="w-4 h-4" />
                <span>Intervention approved by Admin. SCADA valve throttled and logged in audit record.</span>
              </div>
            ) : (
              <div className="text-xs text-coral font-semibold flex items-center gap-1.5">
                <AlertCircle className="w-4 h-4" />
                <span>Intervention rejected. Operation stopped and audit entry recorded.</span>
              </div>
            )}
          </div>
        </div>
      </section>

      {/* Numbers from the Replay */}
      <section id="impact" className="py-20 px-6 max-w-6xl mx-auto space-y-10">
        <div className="text-center max-w-xl mx-auto space-y-2">
          <span className="text-xs font-semibold text-sky-500 uppercase tracking-wider">Ground Truth Proof</span>
          <h2 className="text-3xl font-bold text-ink-900 dark:text-mist">Numbers from the replay</h2>
          <p className="text-xs text-ink-600 dark:text-sky-300">Measured against simulator hidden ground truth</p>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
          <div className="p-6 rounded-card glass-card text-center shadow-glass space-y-1">
            <span className="text-3xl font-extrabold font-mono text-sky-700 dark:text-sky-300">96.0%</span>
            <span className="text-xs font-medium text-ink-900 dark:text-mist block">Detection F1-Score</span>
            <span className="text-[11px] text-ink-600 dark:text-sky-300 block">vs 79.5% threshold baseline</span>
          </div>
          <div className="p-6 rounded-card glass-card text-center shadow-glass space-y-1">
            <span className="text-3xl font-extrabold font-mono text-aqua">97.8%</span>
            <span className="text-xs font-medium text-ink-900 dark:text-mist block">Top-3 Localization</span>
            <span className="text-[11px] text-ink-600 dark:text-sky-300 block">Identifies exact pipe segment</span>
          </div>
          <div className="p-6 rounded-card glass-card text-center shadow-glass space-y-1">
            <span className="text-3xl font-extrabold font-mono text-leaf">8.4%</span>
            <span className="text-xs font-medium text-ink-900 dark:text-mist block">24h Forecast sMAPE</span>
            <span className="text-[11px] text-ink-600 dark:text-sky-300 block">vs 24.6% naive baseline</span>
          </div>
          <div className="p-6 rounded-card glass-card text-center shadow-glass space-y-1">
            <span className="text-3xl font-extrabold font-mono text-ink-900 dark:text-mist">0</span>
            <span className="text-xs font-medium text-ink-900 dark:text-mist block">Equity Violations</span>
            <span className="text-[11px] text-ink-600 dark:text-sky-300 block">100% vulnerable minimum supply met</span>
          </div>
        </div>
      </section>

      {/* Footer Band */}
      <footer className="p-12 border-t border-sky-100 dark:border-white/10 text-center space-y-4">
        <Logo size="md" className="justify-center" />
        <p className="text-xs text-ink-600 dark:text-sky-300">
          NEERARAN • TCS Tech Day 2026 Challenge 12 • AI for Water Resilience & Smart Resource Management
        </p>
        <button
          onClick={() => navigate('/login')}
          className="px-6 py-2.5 rounded-btn bg-sky-500 hover:bg-sky-700 text-white font-semibold text-xs shadow-sm transition-colors"
        >
          Enter Control Center
        </button>
      </footer>
    </div>
  );
};
