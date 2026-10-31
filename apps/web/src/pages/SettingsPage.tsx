import React, { useState } from 'react';
import { Sliders, RotateCcw, Save, ShieldAlert, Wifi, Server } from 'lucide-react';
import { apiFetch } from '../api';
import { useStore } from '../store/useStore';

export const SettingsPage: React.FC = () => {
  const { role } = useStore();
  const [leakThresholdZ, setLeakThresholdZ] = useState<number>(3.0);
  const [vulnSupplyPct, setVulnSupplyPct] = useState<number>(85);
  const [weights, setWeights] = useState({
    loss_rate: 0.30,
    population: 0.20,
    vulnerability: 0.25,
    urgency: 0.15,
    crew_availability: 0.10,
  });
  const [saving, setSaving] = useState(false);
  const [saveStatus, setSaveStatus] = useState<string | null>(null);

  const handleSaveWeights = async () => {
    if (role !== 'admin') {
      alert('Only Estate Admin can update prioritization weights.');
      return;
    }
    setSaving(true);
    try {
      await apiFetch('/v1/prioritizer/weights', {
        method: 'POST',
        body: JSON.stringify({ weights }),
      });
      setSaveStatus('Prioritizer weights successfully applied. Incident queue reordered.');
      setTimeout(() => setSaveStatus(null), 3000);
    } catch (err: any) {
      alert(`Error updating weights: ${err.message}`);
    } finally {
      setSaving(false);
    }
  };

  const handleResetDemo = async () => {
    if (role !== 'admin') {
      alert('Only Estate Admin can reset the demonstration state.');
      return;
    }
    if (confirm('Reset demonstration state to Day 1 08:00 AM? This will clear active approvals and faults.')) {
      try {
        await apiFetch('/v1/simulation/scenarios', {
          method: 'POST',
          body: JSON.stringify({ scenario_name: 'Reset' }),
        });
        window.location.reload();
      } catch (err) {
        window.location.reload();
      }
    }
  };

  return (
    <div className="py-6 px-4 max-w-5xl mx-auto space-y-6">
      {/* Header */}
      <div className="glass-card p-6 shadow-glass flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-ink-900 dark:text-mist">Estate Admin Operational Settings</h1>
          <p className="text-xs text-ink-600 dark:text-sky-300 mt-1">
            Configure hydraulic anomaly thresholds, prioritizer formula weights, and distributed data sources.
          </p>
        </div>

        <button
          onClick={handleResetDemo}
          disabled={role !== 'admin'}
          className="px-4 py-2 rounded-btn bg-coral/10 border border-coral/30 text-coral hover:bg-coral hover:text-white text-xs font-semibold flex items-center gap-2 transition-colors disabled:opacity-50"
        >
          <RotateCcw className="w-3.5 h-3.5" />
          <span>Reset Demo to Day 1</span>
        </button>
      </div>

      {saveStatus && (
        <div className="p-3 bg-leaf/15 border border-leaf/30 rounded-xl text-leaf text-xs font-medium">
          {saveStatus}
        </div>
      )}

      {/* Settings Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        
        {/* Prioritizer Weights */}
        <div className="glass-card p-6 shadow-glass space-y-5">
          <div className="flex items-center justify-between pb-3 border-b border-sky-100 dark:border-white/10">
            <h2 className="text-sm font-bold text-ink-900 dark:text-mist">Prioritizer Formula Weights</h2>
            <span className="text-[11px] font-mono text-ink-600 dark:text-sky-300">Sum: 1.00</span>
          </div>

          <div className="space-y-4 text-xs">
            <div>
              <div className="flex justify-between pb-1 text-ink-900 dark:text-mist">
                <span>Loss Rate Term Weight:</span>
                <span className="font-mono font-bold">{(weights.loss_rate * 100).toFixed(0)}%</span>
              </div>
              <input
                type="range"
                min="0.05"
                max="0.50"
                step="0.05"
                value={weights.loss_rate}
                onChange={(e) => setWeights({ ...weights, loss_rate: parseFloat(e.target.value) })}
                className="w-full accent-sky-500"
                disabled={role !== 'admin'}
              />
            </div>

            <div>
              <div className="flex justify-between pb-1 text-ink-900 dark:text-mist">
                <span>Vulnerability Weight (Hostels / Health):</span>
                <span className="font-mono font-bold">{(weights.vulnerability * 100).toFixed(0)}%</span>
              </div>
              <input
                type="range"
                min="0.10"
                max="0.50"
                step="0.05"
                value={weights.vulnerability}
                onChange={(e) => setWeights({ ...weights, vulnerability: parseFloat(e.target.value) })}
                className="w-full accent-sky-500"
                disabled={role !== 'admin'}
              />
            </div>

            <div>
              <div className="flex justify-between pb-1 text-ink-900 dark:text-mist">
                <span>Population Affected Weight:</span>
                <span className="font-mono font-bold">{(weights.population * 100).toFixed(0)}%</span>
              </div>
              <input
                type="range"
                min="0.05"
                max="0.40"
                step="0.05"
                value={weights.population}
                onChange={(e) => setWeights({ ...weights, population: parseFloat(e.target.value) })}
                className="w-full accent-sky-500"
                disabled={role !== 'admin'}
              />
            </div>

            <button
              onClick={handleSaveWeights}
              disabled={role !== 'admin' || saving}
              className="w-full py-2.5 rounded-btn bg-sky-500 hover:bg-sky-700 text-white font-medium text-xs flex items-center justify-center gap-1.5 shadow-sm transition-colors disabled:opacity-50"
            >
              <Save className="w-3.5 h-3.5" />
              <span>Apply Weights & Re-rank</span>
            </button>
          </div>
        </div>

        {/* Distributed Sources Status */}
        <div className="glass-card p-6 shadow-glass space-y-5">
          <div className="flex items-center justify-between pb-3 border-b border-sky-100 dark:border-white/10">
            <h2 className="text-sm font-bold text-ink-900 dark:text-mist">5-Laptop Distributed Sources</h2>
            <span className="text-[11px] font-mono text-leaf">4 / 4 Registered</span>
          </div>

          <div className="space-y-3 text-xs">
            <div className="p-3 bg-white/70 dark:bg-white/5 rounded-xl flex items-center justify-between">
              <div>
                <span className="font-bold text-ink-900 dark:text-mist block">Source 1: Supply & Reservoirs</span>
                <span className="text-[10px] text-ink-600 dark:text-sky-300">Municipal, Borewells 1-2, Sump</span>
              </div>
              <span className="px-2 py-0.5 rounded-pill bg-leaf/15 text-leaf font-semibold text-[10px]">Online</span>
            </div>

            <div className="p-3 bg-white/70 dark:bg-white/5 rounded-xl flex items-center justify-between">
              <div>
                <span className="font-bold text-ink-900 dark:text-mist block">Source 2: Building Consumption</span>
                <span className="text-[10px] text-ink-600 dark:text-sky-300">20 Block Smart Ultrasonic Meters</span>
              </div>
              <span className="px-2 py-0.5 rounded-pill bg-leaf/15 text-leaf font-semibold text-[10px]">Online</span>
            </div>

            <div className="p-3 bg-white/70 dark:bg-white/5 rounded-xl flex items-center justify-between">
              <div>
                <span className="font-bold text-ink-900 dark:text-mist block">Source 3: Infrastructure SCADA</span>
                <span className="text-[10px] text-ink-600 dark:text-sky-300">Overhead Tanks 1-4, Line Pressures</span>
              </div>
              <span className="px-2 py-0.5 rounded-pill bg-leaf/15 text-leaf font-semibold text-[10px]">Online</span>
            </div>

            <div className="p-3 bg-white/70 dark:bg-white/5 rounded-xl flex items-center justify-between">
              <div>
                <span className="font-bold text-ink-900 dark:text-mist block">Source 4: Operations & Weather</span>
                <span className="text-[10px] text-ink-600 dark:text-sky-300">Weather radar, complaints, engineers</span>
              </div>
              <span className="px-2 py-0.5 rounded-pill bg-leaf/15 text-leaf font-semibold text-[10px]">Online</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
