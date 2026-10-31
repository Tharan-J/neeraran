import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ResponsiveContainer, AreaChart, Area, XAxis, YAxis, Tooltip, BarChart, Bar, LineChart, Line, ReferenceLine } from 'recharts';
import { ArrowUpRight, Check, X, ShieldAlert, Clock, Droplet, AlertTriangle, Layers, Filter } from 'lucide-react';
import { useStore } from '../store/useStore';
import { apiFetch } from '../api';

export const OverviewPage: React.FC = () => {
  const navigate = useNavigate();
  const { role, viewerLens, setViewerLens, simState, setSelectedCaseId } = useStore();
  const [incidents, setIncidents] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [forecastData, setForecastData] = useState<any[]>([]);
  const [nightFlowData, setNightFlowData] = useState<any[]>([]);

  // Fetch incidents & forecast
  const loadData = async () => {
    try {
      setLoading(true);
      const incList = await apiFetch<any[]>('/v1/incidents');
      setIncidents(incList || []);

      const fData = await apiFetch<any>('/v1/forecast');
      if (fData && fData.sump_trajectory_72h) {
        setForecastData(fData.sump_trajectory_72h);
      }
    } catch (err) {
      console.warn('Overview data fetch fallback:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 6000);
    return () => clearInterval(interval);
  }, []);

  // Prepare Night Flow comparison data from simState or defaults
  useEffect(() => {
    if (simState?.block_meters) {
      const nf = [
        { block: 'Hostel A', current: simState.block_meters['BLK-HSTL-A'] || 58.4, baseline: 12.0, flagged: true },
        { block: 'Hostel B', current: simState.block_meters['BLK-HSTL-B'] || 13.2, baseline: 10.0, flagged: false },
        { block: 'Hostel C', current: simState.block_meters['BLK-HSTL-C'] || 15.1, baseline: 14.0, flagged: false },
        { block: 'Mess', current: simState.block_meters['BLK-MESS'] || 9.5, baseline: 8.0, flagged: false },
        { block: 'Health', current: simState.block_meters['BLK-HLTH'] || 3.8, baseline: 3.0, flagged: false },
        { block: 'Acad 1', current: simState.block_meters['BLK-ACAD-1'] || 2.4, baseline: 2.0, flagged: false },
        { block: 'Library', current: simState.block_meters['BLK-LIB'] || 0.0, baseline: 1.0, flagged: true },
      ];
      setNightFlowData(nf);
    } else {
      setNightFlowData([
        { block: 'Hostel A', current: 58.4, baseline: 12.0, flagged: true },
        { block: 'Hostel B', current: 13.2, baseline: 10.0, flagged: false },
        { block: 'Hostel C', current: 15.1, baseline: 14.0, flagged: false },
        { block: 'Mess', current: 9.5, baseline: 8.0, flagged: false },
        { block: 'Health', current: 3.8, baseline: 3.0, flagged: false },
        { block: 'Acad 1', current: 2.4, baseline: 2.0, flagged: false },
        { block: 'Library', current: 0.0, baseline: 1.0, flagged: true },
      ]);
    }
  }, [simState]);

  const handleApprove = async (planId: string) => {
    try {
      await apiFetch(`/v1/approvals/${planId}`, {
        method: 'POST',
        body: JSON.stringify({ decision: 'approved', note: 'Approved by Estate Admin on Overview' }),
      });
      loadData();
    } catch (err: any) {
      alert(`Approval error: ${err.message}`);
    }
  };

  const handleReject = async (planId: string) => {
    try {
      await apiFetch(`/v1/approvals/${planId}`, {
        method: 'POST',
        body: JSON.stringify({ decision: 'rejected', note: 'Rejected by Estate Admin' }),
      });
      loadData();
    } catch (err: any) {
      alert(`Rejection error: ${err.message}`);
    }
  };

  return (
    <div className="py-6 px-4 max-w-7xl mx-auto space-y-6">
      {/* 1. Greeting row & data freshness */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 glass-card p-5 shadow-glass">
        <div>
          <h1 className="text-xl md:text-2xl font-bold text-ink-900 dark:text-mist">
            Good morning, Estate Office
          </h1>
          <p className="text-xs text-ink-600 dark:text-sky-300 font-mono mt-0.5">
            {simState?.formatted_time || 'Saturday, 31 Oct 2026 03:15 UTC'} • Sathyamangalam Digital Twin
          </p>
        </div>

        <div className="flex items-center gap-4">
          {/* Viewer Lens Switcher */}
          {role === 'viewer' && (
            <div className="flex items-center gap-1.5 bg-sky-100/60 dark:bg-white/10 px-3 py-1.5 rounded-pill text-xs">
              <Filter className="w-3.5 h-3.5 text-sky-700 dark:text-sky-300" />
              <span className="text-ink-600 dark:text-sky-300">Lens:</span>
              <select
                value={viewerLens}
                onChange={(e) => setViewerLens(e.target.value as any)}
                className="bg-transparent font-semibold text-sky-700 dark:text-mist outline-none cursor-pointer"
              >
                <option value="warden">Hostels & Warden Lens</option>
                <option value="sustainability">Sustainability Cell</option>
                <option value="student">Student Public Advisory</option>
                <option value="maintenance">Maintenance Work Orders</option>
              </select>
            </div>
          )}

          <div className="text-right">
            <span className="text-[11px] font-mono text-ink-600 dark:text-sky-300 block">
              simulated data, updated 2s ago
            </span>
            <span className="text-xs font-semibold text-aqua">
              Campus Hydraulic Regime: Normal Stable
            </span>
          </div>
        </div>
      </div>

      {/* 2. KPI row of 5 cards */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
        <div className="glass-card p-4 shadow-glass hover:shadow-glass-hover transition-shadow cursor-pointer" onClick={() => navigate('/app/simulation')}>
          <span className="text-[11px] font-medium text-ink-600 dark:text-sky-300 block">Water in reserve</span>
          <div className="flex items-baseline gap-2 mt-1">
            <span className="text-2xl font-bold font-mono text-ink-900 dark:text-mist">{simState?.days_of_reserve || 2.8}</span>
            <span className="text-xs text-ink-600 dark:text-sky-300">days</span>
          </div>
          <span className="text-[10px] text-aqua block mt-1">80% band [2.4 - 3.2 d]</span>
        </div>

        <div className="glass-card p-4 shadow-glass hover:shadow-glass-hover transition-shadow cursor-pointer" onClick={() => navigate('/app/agents')}>
          <span className="text-[11px] font-medium text-ink-600 dark:text-sky-300 block">Active leak cases</span>
          <div className="flex items-baseline gap-2 mt-1">
            <span className="text-2xl font-bold font-mono text-coral">{incidents.filter(i => i.type === 'leak').length || 1}</span>
            <span className="text-xs text-coral">verified</span>
          </div>
          <span className="text-[10px] text-coral block mt-1">PIPE-OHT1-HSTLA localized</span>
        </div>

        <div className="glass-card p-4 shadow-glass hover:shadow-glass-hover transition-shadow cursor-pointer" onClick={() => navigate('/app/map')}>
          <span className="text-[11px] font-medium text-ink-600 dark:text-sky-300 block">Estimated loss today</span>
          <div className="flex items-baseline gap-2 mt-1">
            <span className="text-2xl font-bold font-mono text-ink-900 dark:text-mist">83.5</span>
            <span className="text-xs text-ink-600 dark:text-sky-300">kL/day</span>
          </div>
          <span className="text-[10px] text-amber block mt-1">₹3,507 economic value</span>
        </div>

        <div className="glass-card p-4 shadow-glass hover:shadow-glass-hover transition-shadow cursor-pointer" onClick={() => navigate('/app/evaluation')}>
          <span className="text-[11px] font-medium text-ink-600 dark:text-sky-300 block">Water saved this week</span>
          <div className="flex items-baseline gap-2 mt-1">
            <span className="text-2xl font-bold font-mono text-leaf">184.2</span>
            <span className="text-xs text-leaf">kL</span>
          </div>
          <span className="text-[10px] text-leaf block mt-1">₹7,736 saved</span>
        </div>

        <div className="glass-card p-4 shadow-glass hover:shadow-glass-hover transition-shadow cursor-pointer" onClick={() => navigate('/app/approvals')}>
          <span className="text-[11px] font-medium text-ink-600 dark:text-sky-300 block">Pending approvals</span>
          <div className="flex items-baseline gap-2 mt-1">
            <span className="text-2xl font-bold font-mono text-amber">1</span>
            <span className="text-xs text-amber">action</span>
          </div>
          <span className="text-[10px] text-amber block mt-1">Hostel A valve throttle</span>
        </div>
      </div>

      {/* Main Bento Layout: Left = What to do next, Right = Charts & Sticky note */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* 3. Left Panel: 'What to do next' (Largest Card) */}
        <div className="lg:col-span-2 glass-card p-6 shadow-glass space-y-5">
          <div className="flex items-center justify-between pb-3 border-b border-sky-100 dark:border-white/10">
            <div>
              <h2 className="text-lg font-bold text-ink-900 dark:text-mist">What to do next</h2>
              <p className="text-xs text-ink-600 dark:text-sky-300">Top ranked operational interventions from Prioritizer agent</p>
            </div>
            <span className="px-3 py-1 rounded-pill bg-sky-100 dark:bg-white/10 text-sky-700 dark:text-sky-300 text-xs font-semibold">
              Prioritized Queue
            </span>
          </div>

          <div className="space-y-4">
            {incidents.slice(0, 3).map((inc, idx) => (
              <div
                key={inc.id}
                className="p-4 rounded-xl bg-white/70 dark:bg-white/5 border border-sky-100 dark:border-white/10 space-y-3 hover:border-sky-300 transition-colors"
              >
                <div className="flex items-start justify-between gap-4">
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <span className="w-5 h-5 rounded-full bg-sky-100 dark:bg-white/10 text-sky-700 dark:text-sky-300 text-xs font-bold flex items-center justify-center">
                        {idx + 1}
                      </span>
                      <h3 className="font-bold text-sm text-ink-900 dark:text-mist">
                        {inc.type === 'leak' ? `Isolate & Repair Fissure near ${inc.location}` : `Instrument Recalibration at ${inc.location}`}
                      </h3>
                      <span className={`px-2 py-0.5 rounded-pill text-[10px] font-semibold ${inc.type === 'leak' ? 'bg-coral/15 text-coral' : 'bg-amber/15 text-amber'}`}>
                        Score {inc.priority_score || 88.5}
                      </span>
                    </div>
                    <p className="text-xs text-ink-600 dark:text-sky-300 leading-relaxed pl-7">
                      {inc.why || 'Night flow elevated 58 L/min against 12 L/min baseline. Sub-header pressure collapsed to 2.3 bar.'}
                    </p>
                  </div>
                  <button
                    onClick={() => {
                      setSelectedCaseId(inc.id);
                      navigate('/app/map');
                    }}
                    className="text-xs font-medium text-sky-500 hover:text-sky-700 shrink-0 inline-flex items-center gap-1"
                  >
                    <span>See evidence</span>
                    <ArrowUpRight className="w-3.5 h-3.5" />
                  </button>
                </div>

                <div className="flex items-center justify-between pt-2 pl-7 border-t border-sky-50 dark:border-white/5 text-xs">
                  <span className="text-[11px] text-ink-600 dark:text-sky-300">
                    Impact: Save ~{inc.loss_rate_kl_day || 58.0} kL/day • ₹2,436/d • Gain 9.2 hrs reserve
                  </span>

                  {role === 'admin' ? (
                    <div className="flex items-center gap-2">
                      <button
                        onClick={() => handleApprove(inc.plan_id || 'PLAN-DEFAULT')}
                        className="px-3 py-1 rounded-btn bg-leaf text-white font-medium text-xs hover:opacity-90 flex items-center gap-1"
                      >
                        <Check className="w-3.5 h-3.5" />
                        <span>Approve</span>
                      </button>
                      <button
                        onClick={() => handleReject(inc.plan_id || 'PLAN-DEFAULT')}
                        className="px-3 py-1 rounded-btn bg-coral text-white font-medium text-xs hover:opacity-90 flex items-center gap-1"
                      >
                        <X className="w-3.5 h-3.5" />
                        <span>Reject</span>
                      </button>
                    </div>
                  ) : (
                    <span className="text-[11px] text-ink-600 dark:text-sky-300 italic">
                      Awaiting Estate Admin approval
                    </span>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Right Column: Tilted Sticky note + Activity feed */}
        <div className="space-y-6">
          {/* Slightly tilted 'simulated data' sticky note */}
          <div className="transform -rotate-1 hover:rotate-0 transition-transform bg-[#FFF8D6] text-[#7A6211] p-5 rounded-2xl shadow-sm border border-[#EEDB82]/60 space-y-2 select-none">
            <span className="text-[10px] font-mono tracking-wider uppercase block font-semibold">
              Ground Truth Digital Twin
            </span>
            <p className="text-xs leading-relaxed font-sans">
              All campus telemetry is dynamically generated by physical hydraulic mass-balance equations. Leaks and sensor anomalies reflect real physics.
            </p>
            <div className="text-[10px] font-mono opacity-80 pt-1">
              Seed: 42 • Sathyamangalam Campus
            </div>
          </div>

          {/* Activity & Alert Log */}
          <div className="glass-card p-5 shadow-glass space-y-3">
            <h3 className="text-sm font-bold text-ink-900 dark:text-mist">Operational Activity Log</h3>
            <div className="space-y-2.5 max-h-[280px] overflow-y-auto pr-1">
              <div className="pl-3 border-l-2 border-coral py-0.5 space-y-0.5">
                <span className="text-[10px] font-mono text-ink-600 dark:text-sky-300">03:10 UTC • Detector</span>
                <p className="text-xs text-ink-900 dark:text-mist">Leak candidate opened for Hostel A (58.4 L/min)</p>
              </div>
              <div className="pl-3 border-l-2 border-aqua py-0.5 space-y-0.5">
                <span className="text-[10px] font-mono text-ink-600 dark:text-sky-300">03:11 UTC • Localizer</span>
                <p className="text-xs text-ink-900 dark:text-mist">Top segment ranked: PIPE-OHT1-HSTLA (72% prob)</p>
              </div>
              <div className="pl-3 border-l-2 border-amber py-0.5 space-y-0.5">
                <span className="text-[10px] font-mono text-ink-600 dark:text-sky-300">03:12 UTC • Optimizer</span>
                <p className="text-xs text-ink-900 dark:text-mist">Generated valve throttle plan (0 vulnerable violations)</p>
              </div>
              <div className="pl-3 border-l-2 border-leaf py-0.5 space-y-0.5">
                <span className="text-[10px] font-mono text-ink-600 dark:text-sky-300">03:14 UTC • Verifier</span>
                <p className="text-xs text-ink-900 dark:text-mist">Groundedness confirmed [EVID-101] [EVID-102]</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* 4. Three Recharts Charts */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        
        {/* Chart A: Tank and Sump 72-Hour Forecast with 80% band and safety line */}
        <div className="glass-card p-5 shadow-glass space-y-3">
          <div>
            <h3 className="text-sm font-bold text-ink-900 dark:text-mist">Storage Depletion Forecast</h3>
            <p className="text-[11px] text-ink-600 dark:text-sky-300">72h projection with 80% band & safety limit</p>
          </div>
          <div className="h-48 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={forecastData.length ? forecastData : [
                { hour: 0, forecast_level_kl: 380, lower_bound_80: 360, upper_bound_80: 400, safety_threshold_kl: 100 },
                { hour: 6, forecast_level_kl: 365, lower_bound_80: 340, upper_bound_80: 390, safety_threshold_kl: 100 },
                { hour: 12, forecast_level_kl: 345, lower_bound_80: 315, upper_bound_80: 375, safety_threshold_kl: 100 },
                { hour: 18, forecast_level_kl: 320, lower_bound_80: 285, upper_bound_80: 355, safety_threshold_kl: 100 },
                { hour: 24, forecast_level_kl: 300, lower_bound_80: 260, upper_bound_80: 340, safety_threshold_kl: 100 },
              ]}>
                <XAxis dataKey="hour" tick={{ fontSize: 10 }} stroke="#9EB2C7" />
                <YAxis tick={{ fontSize: 10 }} stroke="#9EB2C7" domain={[0, 500]} />
                <Tooltip contentStyle={{ fontSize: '11px', borderRadius: '12px' }} />
                <ReferenceLine y={100} stroke="#E5594F" strokeDasharray="3 3" label={{ value: 'Safety', fill: '#E5594F', fontSize: 10 }} />
                <Area type="monotone" dataKey="upper_bound_80" stroke="none" fill="#D9E9FB" fillOpacity={0.6} />
                <Area type="monotone" dataKey="lower_bound_80" stroke="none" fill="#D9E9FB" fillOpacity={0.6} />
                <Line type="monotone" dataKey="forecast_level_kl" stroke="#3A8FDA" strokeWidth={2} dot={false} />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Chart B: Minimum Night Flow by Block */}
        <div className="glass-card p-5 shadow-glass space-y-3">
          <div>
            <h3 className="text-sm font-bold text-ink-900 dark:text-mist">Minimum Night Flow by Block</h3>
            <p className="text-[11px] text-ink-600 dark:text-sky-300">Observed 03:00 AM flow vs baseline</p>
          </div>
          <div className="h-48 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={nightFlowData}>
                <XAxis dataKey="block" tick={{ fontSize: 9 }} stroke="#9EB2C7" />
                <YAxis tick={{ fontSize: 10 }} stroke="#9EB2C7" />
                <Tooltip contentStyle={{ fontSize: '11px', borderRadius: '12px' }} />
                <Bar dataKey="baseline" fill="#8FC0EE" name="Baseline (L/min)" radius={[4, 4, 0, 0]} />
                <Bar dataKey="current" fill="#E5594F" name="Current (L/min)" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Chart C: Demand Actual vs Forecast (sMAPE error tracking) */}
        <div className="glass-card p-5 shadow-glass space-y-3">
          <div>
            <h3 className="text-sm font-bold text-ink-900 dark:text-mist">Demand Forecast vs Actual</h3>
            <p className="text-[11px] text-ink-600 dark:text-sky-300">Holt-Winters tracking (sMAPE 8.4%)</p>
          </div>
          <div className="h-48 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={[
                { hour: '00:00', actual: 42, forecast: 40 },
                { hour: '04:00', actual: 18, forecast: 16 },
                { hour: '08:00', actual: 95, forecast: 92 },
                { hour: '12:00', actual: 78, forecast: 80 },
                { hour: '16:00', actual: 64, forecast: 65 },
                { hour: '20:00', actual: 88, forecast: 86 },
              ]}>
                <XAxis dataKey="hour" tick={{ fontSize: 10 }} stroke="#9EB2C7" />
                <YAxis tick={{ fontSize: 10 }} stroke="#9EB2C7" />
                <Tooltip contentStyle={{ fontSize: '11px', borderRadius: '12px' }} />
                <Line type="monotone" dataKey="actual" stroke="#0F2236" strokeWidth={2} dot={{ r: 3 }} name="Actual (L/min)" />
                <Line type="monotone" dataKey="forecast" stroke="#2FB8AA" strokeWidth={2} strokeDasharray="4 4" dot={false} name="Forecast" />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
    </div>
  );
};
