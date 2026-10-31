import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Layers, Activity, AlertCircle, CheckCircle2, ChevronRight, X, Droplet, Gauge, Wrench, Shield } from 'lucide-react';
import { useStore } from '../store/useStore';
import { apiFetch } from '../api';

export const MapPage: React.FC = () => {
  const { role, simState, selectedCaseId, setSelectedCaseId } = useStore();
  const [selectedAsset, setSelectedAsset] = useState<any | null>(null);
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [activeTab, setActiveTab] = useState<'now' | 'why' | 'plan' | 'history'>('why');
  const [layers, setLayers] = useState({
    blocks: true,
    pipes: role !== 'student',
    tanks: true,
    complaints: true
  });
  const [incidents, setIncidents] = useState<any[]>([]);

  useEffect(() => {
    if (role === 'student') {
      setLayers(prev => ({ ...prev, pipes: false }));
    }
  }, [role]);

  useEffect(() => {
    apiFetch<any[]>('/v1/incidents').then((data) => {
      setIncidents(data || []);
      if (data && data.length > 0 && !selectedCaseId) {
        setSelectedCaseId(data[0].id);
      }
    }).catch(() => {});
  }, []);

  const activeCase = incidents.find((i) => i.id === selectedCaseId) || incidents[0] || {
    id: 'CASE-184-LEAK-HSTLA',
    type: 'leak',
    location: 'BLK-HSTL-A',
    confidence: 0.95,
    loss_rate_kl_day: 83.5,
    status: 'investigating',
    why: 'At BLK-HSTL-A, minimum night water flow surged to 58.4 L/min against a historical night baseline of 12.0 L/min. Sub-header pressure dropped to 2.30 bar [EVID-101] [EVID-102].',
    evidence: [
      { id: 'EVID-101', kind: 'night_flow', value: 58.4, baseline: 12.0, unit: 'L/min', note: 'Continuous flow at 03:00 AM' },
      { id: 'EVID-102', kind: 'pressure_drop', value: 2.30, baseline: 2.85, unit: 'bar', note: 'Sub-header depressurization' },
      { id: 'EVID-103', kind: 'water_balance', value: 72.0, baseline: 0.0, unit: 'pct_prob', note: 'Localizer top segment PIPE-OHT1-HSTLA' }
    ],
    verifier_result: 'verified',
    groundedness_score: 1.0
  };

  const handleSelectBlock = (blockId: string, name: string) => {
    setSelectedAsset({ id: blockId, name });
    const matched = incidents.find((i) => i.location === blockId);
    if (matched) {
      setSelectedCaseId(matched.id);
    }
    setDrawerOpen(true);
  };

  return (
    <div className="relative w-full h-[calc(100vh-80px)] overflow-hidden flex flex-col bg-[#F0F5FA] dark:bg-[#0B1622]">
      {/* Top Floating Control Bar */}
      <div className="absolute top-4 left-6 z-20 flex items-center gap-3">
        {/* Layer Toggles */}
        <div className="glass-panel px-4 py-2 rounded-pill shadow-glass flex items-center gap-4 text-xs font-medium">
          <span className="text-ink-600 dark:text-sky-300">Layers:</span>
          <label className="flex items-center gap-1.5 cursor-pointer">
            <input type="checkbox" checked={layers.blocks} onChange={(e) => setLayers({ ...layers, blocks: e.target.checked })} className="rounded text-sky-500" />
            <span>Blocks</span>
          </label>
          {role !== 'student' && (
            <label className="flex items-center gap-1.5 cursor-pointer">
              <input type="checkbox" checked={layers.pipes} onChange={(e) => setLayers({ ...layers, pipes: e.target.checked })} className="rounded text-sky-500" />
              <span>Pipes</span>
            </label>
          )}
          <label className="flex items-center gap-1.5 cursor-pointer">
            <input type="checkbox" checked={layers.tanks} onChange={(e) => setLayers({ ...layers, tanks: e.target.checked })} className="rounded text-sky-500" />
            <span>Tanks</span>
          </label>
          <label className="flex items-center gap-1.5 cursor-pointer">
            <input type="checkbox" checked={layers.complaints} onChange={(e) => setLayers({ ...layers, complaints: e.target.checked })} className="rounded text-sky-500" />
            <span>Complaints</span>
          </label>
        </div>

        {/* Legend */}
        <div className="glass-panel px-3.5 py-2 rounded-pill shadow-glass flex items-center gap-3 text-[11px] font-medium">
          <span className="flex items-center gap-1.5"><span className="w-2.5 h-2.5 rounded-full bg-aqua"></span> Normal</span>
          <span className="flex items-center gap-1.5"><span className="w-2.5 h-2.5 rounded-full bg-amber"></span> Watch</span>
          <span className="flex items-center gap-1.5"><span className="w-2.5 h-2.5 rounded-full bg-coral animate-ping"></span> Leak</span>
        </div>
      </div>

      {/* Main Vector Campus Map Canvas (Digital Twin Fallback Guarantee) */}
      <div className="relative flex-1 w-full h-full flex items-center justify-center p-8 select-none">
        <svg viewBox="0 0 1000 650" className="w-full h-full max-h-[85vh] drop-shadow-md">
          {/* Background Grid Pattern */}
          <pattern id="campus-grid" width="40" height="40" patternUnits="userSpaceOnUse">
            <path d="M 40 0 L 0 0 0 40" fill="none" stroke="rgba(58, 143, 218, 0.08)" strokeWidth="1" />
          </pattern>
          <rect width="1000" height="650" fill="url(#campus-grid)" />

          {/* Pipe Network Lines */}
          {layers.pipes && (
            <g strokeLinecap="round" strokeLinejoin="round">
              {/* Municipal to Sump */}
              <line x1="80" y1="520" x2="480" y2="340" stroke="#3A8FDA" strokeWidth="4" strokeDasharray="6 3" />
              {/* Sump to OHT North */}
              <line x1="480" y1="340" x2="320" y2="180" stroke="#3A8FDA" strokeWidth="5" />
              {/* OHT North to Hostel A (Flagged Leak Pipe Segment) */}
              <line x1="320" y1="180" x2="220" y2="130" stroke="#E5594F" strokeWidth="6" className="pulse-leak" />
              {/* OHT North to Hostel B */}
              <line x1="320" y1="180" x2="380" y2="120" stroke="#2FB8AA" strokeWidth="4" />
              {/* Sump to OHT South (Academic) */}
              <line x1="480" y1="340" x2="680" y2="440" stroke="#3A8FDA" strokeWidth="5" />
              <line x1="680" y1="440" x2="780" y2="420" stroke="#2FB8AA" strokeWidth="4" />
              <line x1="680" y1="440" x2="760" y2="520" stroke="#2FB8AA" strokeWidth="4" />
              {/* Sump to OHT East (Hostel C & Mess) */}
              <line x1="480" y1="340" x2="300" y2="380" stroke="#3A8FDA" strokeWidth="5" />
              <line x1="300" y1="380" x2="180" y2="360" stroke="#2FB8AA" strokeWidth="4" />
              <line x1="300" y1="380" x2="200" y2="440" stroke="#2FB8AA" strokeWidth="4" />
              {/* Sump to OHT West */}
              <line x1="480" y1="340" x2="520" y2="220" stroke="#3A8FDA" strokeWidth="4" />
              <line x1="520" y1="220" x2="640" y2="200" stroke="#2FB8AA" strokeWidth="4" />
            </g>
          )}

          {/* Localization Top-3 Cone around Hostel A */}
          <g>
            <circle cx="270" cy="155" r="38" fill="rgba(229, 89, 79, 0.15)" stroke="#E5594F" strokeWidth="1.5" strokeDasharray="4 2" />
            <circle cx="270" cy="155" r="8" fill="#E5594F" className="pulse-leak" />
            <text x="282" y="152" fill="#E5594F" fontSize="11" fontWeight="bold" fontFamily="sans-serif">
              72% prob [PIPE-OHT1-HSTLA]
            </text>
          </g>

          {/* Campus Block Polygons */}
          {layers.blocks && (
            <g>
              {/* Hostel Block A (Leak highlighted) */}
              <g onClick={() => handleSelectBlock('BLK-HSTL-A', 'Hostel Block A')} className="cursor-pointer group">
                <rect x="150" y="80" width="110" height="75" rx="14" fill="#FFEAE8" stroke="#E5594F" strokeWidth="2.5" />
                <text x="165" y="112" fill="#E5594F" fontSize="12" fontWeight="bold">Hostel A</text>
                <text x="165" y="130" fill="#E5594F" fontSize="10">650 res • Vulnerable</text>
              </g>

              {/* Hostel Block B */}
              <g onClick={() => handleSelectBlock('BLK-HSTL-B', 'Hostel Block B')} className="cursor-pointer">
                <rect x="340" y="80" width="100" height="70" rx="14" fill="#EAF3FD" stroke="#3A8FDA" strokeWidth="1.5" />
                <text x="355" y="112" fill="#0F2236" fontSize="11" fontWeight="bold">Hostel B</text>
                <text x="355" y="128" fill="#4A5F75" fontSize="9">600 res</text>
              </g>

              {/* Central Mess & Kitchen */}
              <g onClick={() => handleSelectBlock('BLK-MESS', 'Central Mess')} className="cursor-pointer">
                <rect x="140" y="330" width="110" height="80" rx="14" fill="#EAF3FD" stroke="#3A8FDA" strokeWidth="1.5" />
                <text x="160" y="365" fill="#0F2236" fontSize="12" fontWeight="bold">Central Mess</text>
                <text x="160" y="385" fill="#4A5F75" fontSize="10">2,000 meals/d</text>
              </g>

              {/* Hostel Block C (Girls) */}
              <g onClick={() => handleSelectBlock('BLK-HSTL-C', 'Hostel Block C')} className="cursor-pointer">
                <rect x="140" y="430" width="110" height="75" rx="14" fill="#EAF3FD" stroke="#3A8FDA" strokeWidth="1.5" />
                <text x="160" y="465" fill="#0F2236" fontSize="12" fontWeight="bold">Hostel C</text>
                <text x="160" y="485" fill="#4A5F75" fontSize="10">750 res • Vulnerable</text>
              </g>

              {/* Academic Blocks 1-4 */}
              <g onClick={() => handleSelectBlock('BLK-ACAD-1', 'Academic Block 1')} className="cursor-pointer">
                <rect x="740" y="380" width="115" height="75" rx="14" fill="#EAF3FD" stroke="#3A8FDA" strokeWidth="1.5" />
                <text x="755" y="415" fill="#0F2236" fontSize="12" fontWeight="bold">Acad 1 (CS/IT)</text>
                <text x="755" y="435" fill="#4A5F75" fontSize="10">1,200 students</text>
              </g>

              <g onClick={() => handleSelectBlock('BLK-ACAD-2', 'Academic Block 2')} className="cursor-pointer">
                <rect x="740" y="480" width="115" height="75" rx="14" fill="#EAF3FD" stroke="#3A8FDA" strokeWidth="1.5" />
                <text x="755" y="515" fill="#0F2236" fontSize="12" fontWeight="bold">Acad 2 (Mech)</text>
                <text x="755" y="535" fill="#4A5F75" fontSize="10">1,000 students</text>
              </g>

              {/* Central Library */}
              <g onClick={() => handleSelectBlock('BLK-LIB', 'Central Library')} className="cursor-pointer">
                <rect x="620" y="310" width="95" height="65" rx="14" fill="#FFF8E8" stroke="#F2A33A" strokeWidth="1.5" />
                <text x="635" y="342" fill="#7A6211" fontSize="11" fontWeight="bold">Library</text>
                <text x="635" y="358" fill="#F2A33A" fontSize="9">Sensor watch (0 L/m)</text>
              </g>

              {/* Campus Health Centre */}
              <g onClick={() => handleSelectBlock('BLK-HLTH', 'Health Centre')} className="cursor-pointer">
                <rect x="610" y="170" width="95" height="60" rx="14" fill="#EAF3FD" stroke="#3A8FDA" strokeWidth="1.5" />
                <text x="625" y="200" fill="#0F2236" fontSize="11" fontWeight="bold">Health Centre</text>
                <text x="625" y="218" fill="#4A5F75" fontSize="9">Vulnerable • 80 beds</text>
              </g>
            </g>
          )}

          {/* Tanks & Storage Points */}
          {layers.tanks && (
            <g>
              {/* Central Ground Sump */}
              <g onClick={() => handleSelectBlock('SUMP-CENTRAL', 'Central Ground Sump')} className="cursor-pointer">
                <circle cx="480" cy="340" r="28" fill="#3A8FDA" stroke="#1E5FA8" strokeWidth="3" />
                <text x="445" y="385" fill="#1E5FA8" fontSize="11" fontWeight="bold">Central Sump (380 kL)</text>
              </g>

              {/* OHT North */}
              <g onClick={() => handleSelectBlock('OHT-NORTH', 'OHT North (Hostels)')} className="cursor-pointer">
                <rect x="305" y="165" width="30" height="30" rx="6" fill="#8FC0EE" stroke="#3A8FDA" strokeWidth="2" />
                <text x="290" y="210" fill="#0F2236" fontSize="10" fontWeight="bold">OHT North (92 kL)</text>
              </g>

              {/* OHT South */}
              <g onClick={() => handleSelectBlock('OHT-SOUTH', 'OHT South (Acad)')} className="cursor-pointer">
                <rect x="665" y="425" width="30" height="30" rx="6" fill="#8FC0EE" stroke="#3A8FDA" strokeWidth="2" />
                <text x="650" y="470" fill="#0F2236" fontSize="10" fontWeight="bold">OHT South (78 kL)</text>
              </g>
            </g>
          )}
        </svg>
      </div>

      {/* 4-Tab Side Drawer (Slides in 280ms) */}
      <AnimatePresence>
        {drawerOpen && (
          <motion.div
            initial={{ x: '100%' }}
            animate={{ x: 0 }}
            exit={{ x: '100%' }}
            transition={{ duration: 0.28, ease: 'easeOut' }}
            className="absolute top-0 right-0 w-full max-w-md h-full z-30 glass-card bg-white/95 dark:bg-[#0F2236]/95 border-l border-white/60 dark:border-white/10 shadow-2xl p-6 flex flex-col space-y-4"
          >
            {/* Drawer Header */}
            <div className="flex items-center justify-between pb-3 border-b border-sky-100 dark:border-white/10">
              <div>
                <span className="text-[10px] font-mono text-ink-600 dark:text-sky-300 uppercase">Case Inspection</span>
                <h3 className="text-base font-bold text-ink-900 dark:text-mist">
                  {selectedAsset?.name || 'Hostel Block A Fissure'}
                </h3>
              </div>
              <button
                onClick={() => setDrawerOpen(false)}
                className="p-1.5 rounded-full hover:bg-sky-100 dark:hover:bg-white/10 text-ink-600 dark:text-sky-300"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            {/* Role-Specific Content */}
            {role === 'student' ? (
              <div className="space-y-4 flex-1 overflow-y-auto pr-1 text-xs">
                <div className="p-4 bg-sky-50 dark:bg-white/5 rounded-2xl border border-sky-100 dark:border-white/10 space-y-2">
                  <span className="font-bold text-ink-900 dark:text-mist text-sm">{selectedAsset?.name || 'Hostel Block A'}</span>
                  <p className="text-ink-600 dark:text-sky-300">
                    Water supply status is actively supervised by the NEERARAN SCADA network.
                  </p>
                </div>
                <div className="grid grid-cols-2 gap-3">
                  <div className="p-3 bg-sky-50/60 dark:bg-white/5 rounded-xl">
                    <span className="text-[11px] text-ink-500 dark:text-sky-400 block">Supply State</span>
                    <span className="text-sm font-bold text-leaf font-mono">Normal Supply</span>
                  </div>
                  <div className="p-3 bg-sky-50/60 dark:bg-white/5 rounded-xl">
                    <span className="text-[11px] text-ink-500 dark:text-sky-400 block">Reserve Autonomy</span>
                    <span className="text-sm font-bold text-ink-900 dark:text-mist font-mono">18.5 hours</span>
                  </div>
                </div>
                <div className="p-3 bg-emerald-50/60 dark:bg-emerald-950/20 border border-emerald-100 dark:border-emerald-800/30 rounded-xl space-y-1">
                  <span className="font-bold text-emerald-800 dark:text-emerald-300">Water Quality: Safe</span>
                  <p className="text-ink-600 dark:text-sky-300 text-[11px]">
                    Chlorine and turbidity transducers within Indian Standard IS 10500 potable limits.
                  </p>
                </div>
                <a
                  href="/app/overview"
                  className="w-full py-2.5 rounded-btn bg-sky-500 text-white font-medium text-xs flex items-center justify-center gap-1.5 hover:bg-sky-600 transition-colors"
                >
                  <Droplet className="w-3.5 h-3.5" />
                  <span>Report Water Issue in this Block</span>
                </a>
              </div>
            ) : (
              <>
                {/* 4 Tab Switcher: Now, Why, Plan, History */}
                <div className="grid grid-cols-4 gap-1 p-1 bg-sky-50 dark:bg-white/5 rounded-xl text-xs font-semibold">
                  {(['now', 'why', 'plan', 'history'] as const).map((tab) => (
                    <button
                      key={tab}
                      onClick={() => setActiveTab(tab)}
                      className={`py-1.5 rounded-lg capitalize transition-colors ${
                        activeTab === tab
                          ? 'bg-white dark:bg-sky-500 text-sky-700 dark:text-white shadow-sm'
                          : 'text-ink-600 dark:text-sky-300 hover:text-ink-900'
                      }`}
                    >
                      {tab}
                    </button>
                  ))}
                </div>
              </>
            )}

            {role !== 'student' && (
              <>
                {/* Tab 1: Now (Live readings) */}
                {activeTab === 'now' && (
                  <div className="space-y-4 flex-1 overflow-y-auto pr-1">
                    <div className="grid grid-cols-2 gap-3">
                      <div className="p-3 bg-sky-50/60 dark:bg-white/5 rounded-xl">
                        <span className="text-[11px] text-ink-600 dark:text-sky-300 block">Meter Flow</span>
                        <span className="text-lg font-bold font-mono text-coral">58.4 L/min</span>
                        <span className="text-[10px] text-coral block mt-0.5">+380% above night baseline</span>
                      </div>
                      <div className="p-3 bg-sky-50/60 dark:bg-white/5 rounded-xl">
                        <span className="text-[11px] text-ink-600 dark:text-sky-300 block">Sub-header Pressure</span>
                        <span className="text-lg font-bold font-mono text-amber">2.30 bar</span>
                        <span className="text-[10px] text-amber block mt-0.5">Nominal 2.85 bar</span>
                      </div>
                    </div>
                    <div className="p-3 bg-sky-50/60 dark:bg-white/5 rounded-xl space-y-1 text-xs">
                      <span className="font-semibold text-ink-900 dark:text-mist block">Data Quality Note:</span>
                      <p className="text-ink-600 dark:text-sky-300">
                        Transducer calibration valid. No flat-line or dropout detected. Signal corroborated by acoustic sensor on PIPE-OHT1-HSTLA.
                      </p>
                    </div>
                  </div>
                )}

                {/* Tab 2: Why (Plain-language reasoning with evidence chips) */}
                {activeTab === 'why' && (
                  <div className="space-y-4 flex-1 overflow-y-auto pr-1">
                    <div className="p-4 bg-sky-50/70 dark:bg-white/5 rounded-2xl border border-sky-100 dark:border-white/10 space-y-3">
                      <div className="flex items-center justify-between">
                        <span className="text-xs font-bold text-sky-700 dark:text-sky-300">Operational Reasoning</span>
                        <span className="px-2 py-0.5 rounded-pill bg-leaf/15 text-leaf text-[10px] font-bold">
                          Verifier Score: 1.0 (Grounded)
                        </span>
                      </div>
                      <p className="text-xs text-ink-900 dark:text-mist leading-relaxed font-sans">
                        {activeCase.why}
                      </p>
                    </div>

                    <div className="space-y-2">
                      <span className="text-xs font-semibold text-ink-900 dark:text-mist block">Supporting Evidence Chips:</span>
                      <div className="space-y-2">
                        {activeCase.evidence?.map((e: any) => (
                          <div key={e.id} className="p-3 bg-white dark:bg-white/5 border border-sky-100 dark:border-white/10 rounded-xl text-xs space-y-1">
                            <div className="flex items-center justify-between">
                              <span className="font-mono font-bold text-sky-700 dark:text-sky-300">[{e.id}] {e.kind}</span>
                              <span className="font-mono text-ink-900 dark:text-mist font-semibold">{e.value} {e.unit} (baseline {e.baseline})</span>
                            </div>
                            <p className="text-[11px] text-ink-600 dark:text-sky-300">{e.note}</p>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                )}

                {/* Tab 3: Plan */}
                {activeTab === 'plan' && (
                  <div className="space-y-4 flex-1 overflow-y-auto pr-1">
                    <div className="space-y-2.5">
                      <span className="text-xs font-semibold text-ink-900 dark:text-mist block">Optimizer Recommended Steps:</span>
                      <div className="p-3 bg-white dark:bg-white/5 border border-sky-100 dark:border-white/10 rounded-xl space-y-1 text-xs">
                        <span className="font-bold text-ink-900 dark:text-mist">Step 1: Create CMMS Work Order</span>
                        <p className="text-ink-600 dark:text-sky-300">Dispatched to K. Priya (Leak Specialist) with pipe clamp kit.</p>
                      </div>
                      <div className="p-3 bg-amber/10 border border-amber/30 rounded-xl space-y-1 text-xs">
                        <span className="font-bold text-amber">Step 2: Throttle Valve VALVE-FEED-HSTLA to 40%</span>
                        <p className="text-ink-600 dark:text-sky-300">Requires Admin approval. Suppresses loss by 45 L/min.</p>
                      </div>
                      <div className="p-3 bg-white dark:bg-white/5 border border-sky-100 dark:border-white/10 rounded-xl space-y-1 text-xs">
                        <span className="font-bold text-ink-900 dark:text-mist">Step 3: Rollback Procedure</span>
                        <p className="text-ink-600 dark:text-sky-300">In case of pressure drop below 1.8 bar, valve returns to 100% open.</p>
                      </div>
                    </div>
                  </div>
                )}

                {/* Tab 4: History */}
                {activeTab === 'history' && (
                  <div className="space-y-3 flex-1 overflow-y-auto pr-1 text-xs">
                    <div className="p-3 bg-sky-50 dark:bg-white/5 rounded-xl space-y-1">
                      <span className="font-mono text-ink-600 dark:text-sky-300">14 days ago • HIST-01</span>
                      <p className="font-medium text-ink-900 dark:text-mist">Hostel B 3rd floor riser repaired by clamp. Cost: ₹4,500.</p>
                    </div>
                    <div className="p-3 bg-sky-50 dark:bg-white/5 rounded-xl space-y-1">
                      <span className="font-mono text-ink-600 dark:text-sky-300">28 days ago • HIST-02</span>
                      <p className="font-medium text-ink-900 dark:text-mist">Transfer pipe joint gasket replaced. Cost: ₹12,800.</p>
                    </div>
                  </div>
                )}
              </>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};
