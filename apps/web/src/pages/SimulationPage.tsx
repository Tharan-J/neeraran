import React, { useState } from 'react';
import { Play, Pause, FastForward, RotateCcw, AlertTriangle, ArrowRight, Check, Send, Sparkles, RefreshCw } from 'lucide-react';
import { apiFetch } from '../api';
import { useStore } from '../store/useStore';

export const SimulationPage: React.FC = () => {
  const { role, simState } = useStore();
  const [speed, setSpeed] = useState<number>(1);
  const [isRunning, setIsRunning] = useState<boolean>(true);
  const [scenarioText, setScenarioText] = useState<string>('');
  const [parseResult, setParseResult] = useState<any | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [replanningDiff, setReplanningDiff] = useState<any | null>(null);

  const presetScenarios = [
    { name: 'Hostel night leak', desc: '58 L/min fissure on Hostel A 2nd floor pipe riser at 03:00 AM' },
    { name: 'Heatwave plus borewell decline', desc: '+4.5°C heatwave, +25% campus demand, -35% borewell yield' },
    { name: 'Monsoon failure', desc: 'Dry spell with 0 mm rainfall and 40% municipal supply reduction' },
    { name: 'Fest weekend occupancy surge', desc: 'Cultural fest surge (+45% occupancy across Hostels & Mess)' },
    { name: 'Main burst plus meter fault', desc: 'Transfer pipe burst (140 L/min) concurrent with Library meter flat-zero dropout' },
  ];

  const handleSpeedChange = async (newSpeed: number) => {
    setSpeed(newSpeed);
    try {
      await apiFetch('/v1/simulation/control', {
        method: 'POST',
        body: JSON.stringify({ speed: newSpeed }),
      });
    } catch (err) {}
  };

  const handleTogglePlay = async () => {
    const next = !isRunning;
    setIsRunning(next);
    try {
      await apiFetch('/v1/simulation/control', {
        method: 'POST',
        body: JSON.stringify({ is_running: next }),
      });
    } catch (err) {}
  };

  const handleLoadPreset = async (scenarioName: string) => {
    setLoading(true);
    try {
      const resp = await apiFetch<any>('/v1/simulation/scenarios', {
        method: 'POST',
        body: JSON.stringify({ scenario_name: scenarioName }),
      });
      setReplanningDiff(resp.replanning_diff);
    } catch (err: any) {
      alert(`Error loading scenario: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleParseScenario = async () => {
    if (!scenarioText.trim()) return;
    setLoading(true);
    try {
      const res = await apiFetch<any>('/v1/simulation/events', {
        method: 'POST',
        body: JSON.stringify({ scenario_text: scenarioText }),
      });
      setParseResult(res);
    } catch (err: any) {
      alert(`Error parsing scenario: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleExecuteParsedEvents = async () => {
    if (!parseResult || !parseResult.parsed_events) return;
    setLoading(true);
    try {
      const firstEv = parseResult.parsed_events[0];
      const res = await apiFetch<any>('/v1/simulation/events', {
        method: 'POST',
        body: JSON.stringify({
          event_type: firstEv.event_type,
          location: firstEv.location,
          params: firstEv.params,
        }),
      });
      setReplanningDiff(res.diff);
      setParseResult(null);
      setScenarioText('');
    } catch (err: any) {
      alert(`Error applying parsed scenario: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="py-6 px-4 max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div className="glass-card p-6 shadow-glass flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <span className="text-[11px] font-mono text-sky-500 uppercase font-semibold">TCS Capability 5: Adaptability</span>
          <h1 className="text-2xl font-bold text-ink-900 dark:text-mist">Scenario Simulation & Re-Planning</h1>
          <p className="text-xs text-ink-600 dark:text-sky-300 mt-1">
            Dynamic scenario injector and real-time replanning engine for unseen operational regimes.
          </p>
        </div>

        {/* Speed Controls */}
        <div className="flex items-center gap-3">
          <button
            onClick={handleTogglePlay}
            className="p-2.5 rounded-pill bg-sky-500 text-white shadow-sm hover:bg-sky-700 transition-colors"
          >
            {isRunning ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4" />}
          </button>

          <div className="flex items-center gap-1 bg-sky-100/60 dark:bg-white/10 p-1 rounded-pill text-xs font-semibold">
            {[1, 5, 20].map((s) => (
              <button
                key={s}
                onClick={() => handleSpeedChange(s)}
                className={`px-3 py-1 rounded-pill transition-colors ${
                  speed === s ? 'bg-white dark:bg-sky-500 text-sky-700 dark:text-white shadow-sm' : 'text-ink-600 dark:text-sky-300'
                }`}
              >
                {s}x
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Main Grid: Left = Presets & Free text, Right = What Changed Diff */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        
        {/* Left Column: Preset Scenarios & Natural Language Injector */}
        <div className="space-y-6">
          {/* Preset Scenarios */}
          <div className="glass-card p-6 shadow-glass space-y-4">
            <h2 className="text-base font-bold text-ink-900 dark:text-mist">Preset Benchmark Scenarios</h2>
            <div className="space-y-2.5">
              {presetScenarios.map((sc) => (
                <div
                  key={sc.name}
                  className="p-3.5 bg-white/70 dark:bg-white/5 border border-sky-100 dark:border-white/10 rounded-xl flex items-center justify-between gap-4 hover:border-sky-300 transition-colors"
                >
                  <div className="space-y-0.5">
                    <span className="text-xs font-bold text-ink-900 dark:text-mist block">{sc.name}</span>
                    <p className="text-[11px] text-ink-600 dark:text-sky-300">{sc.desc}</p>
                  </div>
                  <button
                    onClick={() => handleLoadPreset(sc.name)}
                    disabled={role !== 'admin' || loading}
                    className="px-4 py-1.5 rounded-btn bg-sky-500 text-white text-xs font-medium hover:bg-sky-700 disabled:opacity-50 transition-colors shrink-0"
                  >
                    Load & Replan
                  </button>
                </div>
              ))}
            </div>
          </div>

          {/* Natural Language Free-Text Scenario Injector (Jury Surprise) */}
          <div className="glass-card p-6 shadow-glass space-y-4">
            <div className="flex items-center gap-2">
              <Sparkles className="w-4 h-4 text-sky-500" />
              <h2 className="text-base font-bold text-ink-900 dark:text-mist">Jury Free-Text Scenario Injector</h2>
            </div>
            <p className="text-xs text-ink-600 dark:text-sky-300">
              Type any unseen situation in natural language. Gemini AI converts it into structured operational events.
            </p>

            <div className="space-y-3">
              <textarea
                value={scenarioText}
                onChange={(e) => setScenarioText(e.target.value)}
                placeholder="e.g. Hostel A 2nd floor pipe fissure losing 60 liters per min, or Heatwave for 3 days..."
                rows={3}
                className="w-full p-3 rounded-xl glass-panel border border-sky-200 dark:border-white/10 text-xs text-ink-900 dark:text-mist outline-none focus:border-sky-500 resize-none font-sans"
              />

              <button
                onClick={handleParseScenario}
                disabled={role !== 'admin' || !scenarioText.trim() || loading}
                className="w-full py-2.5 rounded-btn bg-sky-500 hover:bg-sky-700 text-white font-medium text-xs shadow-sm transition-colors flex items-center justify-center gap-2 disabled:opacity-50"
              >
                <Send className="w-3.5 h-3.5" />
                <span>Parse Scenario with Gemini</span>
              </button>
            </div>

            {/* Confirmation Card before Execution */}
            {parseResult && (
              <div className="p-4 bg-sky-50 dark:bg-white/5 rounded-2xl border border-sky-200 dark:border-white/10 space-y-3 text-xs">
                <span className="font-bold text-sky-700 dark:text-sky-300 block">Confirmation Card</span>
                <p className="text-ink-900 dark:text-mist">{parseResult.confirmation_text}</p>
                <pre className="p-2.5 bg-white dark:bg-black/20 rounded-lg text-[11px] font-mono text-ink-600 dark:text-sky-300 overflow-x-auto">
                  {JSON.stringify(parseResult.parsed_events, null, 2)}
                </pre>
                <div className="flex items-center justify-end gap-2 pt-1">
                  <button
                    onClick={() => setParseResult(null)}
                    className="px-3 py-1.5 rounded-btn bg-gray-200 dark:bg-white/10 text-ink-600 dark:text-mist font-medium"
                  >
                    Edit
                  </button>
                  <button
                    onClick={handleExecuteParsedEvents}
                    className="px-4 py-1.5 rounded-btn bg-leaf text-white font-semibold flex items-center gap-1 shadow-sm"
                  >
                    <Check className="w-3.5 h-3.5" />
                    <span>Run & Adapt Plan</span>
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Right Column: What Changed Dynamic Diff Card */}
        <div className="space-y-6">
          <div className="glass-card p-6 shadow-glass space-y-5">
            <div className="flex items-center justify-between pb-3 border-b border-sky-100 dark:border-white/10">
              <h2 className="text-base font-bold text-ink-900 dark:text-mist">What Changed Panel</h2>
              <span className="px-3 py-1 rounded-pill bg-leaf/15 text-leaf text-xs font-semibold">
                Autonomous Adaptation
              </span>
            </div>

            {replanningDiff ? (
              <div className="space-y-4 text-xs">
                <div className="p-3.5 rounded-xl bg-sky-50/70 dark:bg-white/5 space-y-1">
                  <span className="font-semibold text-sky-700 dark:text-sky-300 block">Adaptation Trigger:</span>
                  <p className="text-ink-900 dark:text-mist">{replanningDiff.reason_for_change}</p>
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div className="p-3 bg-white/70 dark:bg-white/5 rounded-xl space-y-1">
                    <span className="text-[11px] text-ink-600 dark:text-sky-300 block">Agents Rerun:</span>
                    <span className="font-mono font-bold text-leaf">
                      {replanningDiff.agents_rerun?.join(', ')}
                    </span>
                  </div>
                  <div className="p-3 bg-white/70 dark:bg-white/5 rounded-xl space-y-1">
                    <span className="text-[11px] text-ink-600 dark:text-sky-300 block">Recovery Time:</span>
                    <span className="font-mono font-bold text-sky-700 dark:text-sky-300">
                      {replanningDiff.recovery_timer_seconds} seconds
                    </span>
                  </div>
                </div>

                <div className="p-3 rounded-xl bg-white/70 dark:bg-white/5 space-y-1">
                  <span className="font-semibold text-ink-900 dark:text-mist block">Updated Prioritized Sequence:</span>
                  <div className="flex items-center gap-2 font-mono text-[11px] text-sky-700 dark:text-sky-300">
                    <span>{replanningDiff.new_ranked_cases?.join(' → ') || 'All cases re-optimized'}</span>
                  </div>
                </div>
              </div>
            ) : (
              <div className="p-12 text-center text-xs text-ink-600 dark:text-sky-300 space-y-2">
                <RefreshCw className="w-8 h-8 text-sky-500 mx-auto opacity-60" />
                <p className="font-semibold text-sm text-ink-900 dark:text-mist">Standing by for Scenario Injection</p>
                <p>Select any preset benchmark scenario or enter free-text to view dynamic adaptation metrics.</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
