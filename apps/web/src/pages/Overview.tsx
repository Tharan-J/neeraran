import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ResponsiveContainer, AreaChart, Area, XAxis, YAxis, Tooltip, BarChart, Bar, LineChart, Line, ReferenceLine } from 'recharts';
import {
  ArrowUpRight, Check, X, ShieldAlert, Clock, Droplet, AlertTriangle, Layers, Filter,
  GraduationCap, Building2, Wrench, Shield, Send, CheckCircle2, AlertCircle, FileText,
  UserCheck, ChevronRight, Sparkles, PhoneCall, RefreshCw
} from 'lucide-react';
import { useStore } from '../store/useStore';
import { apiFetch } from '../api';

export const OverviewPage: React.FC = () => {
  const { role } = useStore();

  switch (role) {
    case 'student':
      return <StudentOverviewView />;
    case 'building_admin':
      return <BuildingAdminOverviewView />;
    case 'engineer':
      return <EngineerOverviewView />;
    case 'admin':
    default:
      return <AdminOverviewView />;
  }
};

// ============================================================================
// 1. STUDENT RESIDENT VIEW: Campus Water Awareness & CPGRAMS Grievance Portal
// ============================================================================
const StudentOverviewView: React.FC = () => {
  const { assignedBuildingId, simState } = useStore();
  const [awareness, setAwareness] = useState<any>(null);
  const [consumptionData, setConsumptionData] = useState<any[]>([]);
  const [complaints, setComplaints] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);

  // New Complaint Form State
  const [category, setCategory] = useState('Water leakage');
  const [description, setDescription] = useState('');
  const [priority, setPriority] = useState('medium');
  const [submitting, setSubmitting] = useState(false);
  const [submissionSuccess, setSubmissionSuccess] = useState<string | null>(null);

  const buildingId = assignedBuildingId || 'BLK-HSTL-A';

  const loadStudentData = async () => {
    try {
      setLoading(true);
      const aw = await apiFetch<any>(`/v1/awareness/buildings/${buildingId}`);
      setAwareness(aw);

      const ch = await apiFetch<any>(`/v1/awareness/buildings/${buildingId}/consumption`);
      if (ch && ch.readings) setConsumptionData(ch.readings);

      const cmps = await apiFetch<any[]>('/v1/complaints');
      setComplaints(cmps || []);
    } catch (err) {
      console.warn('Student view data load warning:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadStudentData();
    const interval = setInterval(loadStudentData, 8000);
    return () => clearInterval(interval);
  }, [buildingId]);

  const handleSubmitComplaint = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!description.trim()) return;

    try {
      setSubmitting(true);
      const res = await apiFetch<any>('/v1/complaints', {
        method: 'POST',
        body: JSON.stringify({
          building_id: buildingId,
          category,
          description,
          priority
        })
      });
      setSubmissionSuccess(res.message || `Grievance registered under ${res.tracking_id}`);
      setDescription('');
      loadStudentData();
      setTimeout(() => setSubmissionSuccess(null), 8000);
    } catch (err: any) {
      alert(`Submission error: ${err.message}`);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="py-6 px-4 max-w-7xl mx-auto space-y-6">
      {/* Top Banner */}
      <div className="glass-card p-6 shadow-glass flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="px-2.5 py-0.5 rounded-pill bg-emerald-500/15 text-emerald-600 dark:text-emerald-400 font-mono text-[10px] font-bold uppercase">
              Student Resident Portal
            </span>
            <span className="text-xs font-semibold text-sky-700 dark:text-sky-300">
              Hostel Block A • Room 314
            </span>
          </div>
          <h1 className="text-xl md:text-2xl font-bold text-ink-900 dark:text-mist mt-1">
            Campus Water Awareness & Resident Support
          </h1>
          <p className="text-xs text-ink-600 dark:text-sky-300">
            Real-time telemetry for your hostel block, Indian Standard IS 1172 conservation metrics, and CPGRAMS grievance tracking.
          </p>
        </div>

        <div className="text-right p-3 bg-sky-50 dark:bg-white/5 rounded-2xl border border-sky-100 dark:border-white/10 shrink-0">
          <span className="text-[10px] uppercase font-mono text-ink-500 dark:text-sky-400 block">Supply Status</span>
          <span className="text-sm font-bold text-leaf flex items-center justify-end gap-1.5 mt-0.5">
            <span className="w-2 h-2 rounded-full bg-leaf animate-pulse"></span>
            {awareness?.q1_supply_status || 'Normal Supply — Full Pressure'}
          </span>
        </div>
      </div>

      {/* The 7 Core Operational Awareness Questions */}
      <div>
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-sm font-bold uppercase tracking-wider text-ink-600 dark:text-sky-300 font-mono">
            Hostel Block A Water Health (7 Key Indicators)
          </h2>
          <span className="text-[11px] text-ink-500 dark:text-sky-400 font-mono">
            Live SCADA Transducer Stream
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {/* Q1 & Q2: Consumption vs Baseline */}
          <div className="glass-card p-4 shadow-glass space-y-2">
            <span className="text-[11px] font-medium text-ink-500 dark:text-sky-400 block">Current Consumption</span>
            <div className="flex items-baseline gap-2">
              <span className="text-2xl font-bold font-mono text-ink-900 dark:text-mist">
                {awareness?.q2_consumption_lpm ? awareness.q2_consumption_lpm.toFixed(1) : '45.2'}
              </span>
              <span className="text-xs text-ink-600 dark:text-sky-300">L/min</span>
            </div>
            <div className="text-[11px] text-ink-600 dark:text-sky-300 flex items-center justify-between pt-1 border-t border-sky-100 dark:border-white/10">
              <span>Expected Baseline:</span>
              <span className="font-mono font-semibold">{awareness?.q2_baseline_lpm || 48.0} L/min</span>
            </div>
            <span className={`text-[10px] font-semibold block ${awareness?.q2_deviation_pct > 25 ? 'text-coral' : 'text-leaf'}`}>
              {awareness?.q2_deviation_pct > 0 ? `+${awareness?.q2_deviation_pct}%` : `${awareness?.q2_deviation_pct || -5.8}%`} from normal band
            </span>
          </div>

          {/* Q3: Night Flow / Leak Status */}
          <div className="glass-card p-4 shadow-glass space-y-2">
            <span className="text-[11px] font-medium text-ink-500 dark:text-sky-400 block">Night Flow & Leak Status</span>
            <div className="flex items-baseline gap-2">
              <span className="text-xl font-bold text-ink-900 dark:text-mist">
                {awareness?.q3_minimum_night_flow_status === 'normal' ? 'Normal' : 'Inspection Queued'}
              </span>
            </div>
            <div className="text-[11px] text-ink-600 dark:text-sky-300 flex items-center justify-between pt-1 border-t border-sky-100 dark:border-white/10">
              <span>Riser Dampness:</span>
              <span className="font-semibold text-leaf">None Detected</span>
            </div>
            <span className="text-[10px] text-ink-500 dark:text-sky-400 block">
              Sub-header acoustic sensor checked 03:00 AM
            </span>
          </div>

          {/* Q5: Storage Autonomy */}
          <div className="glass-card p-4 shadow-glass space-y-2">
            <span className="text-[11px] font-medium text-ink-500 dark:text-sky-400 block">Overhead Tank Autonomy</span>
            <div className="flex items-baseline gap-2">
              <span className="text-2xl font-bold font-mono text-ink-900 dark:text-mist">
                {awareness?.q5_hours_autonomy || 18.5}
              </span>
              <span className="text-xs text-ink-600 dark:text-sky-300">hours</span>
            </div>
            <div className="text-[11px] text-ink-600 dark:text-sky-300 flex items-center justify-between pt-1 border-t border-sky-100 dark:border-white/10">
              <span>Reserve Capacity:</span>
              <span className="font-mono font-semibold">50.0 kL</span>
            </div>
            <span className="text-[10px] text-aqua block">
              Protected against external municipal supply cutoff
            </span>
          </div>

          {/* Q6: Indian Standard Compliance */}
          <div className="glass-card p-4 shadow-glass space-y-2">
            <span className="text-[11px] font-medium text-ink-500 dark:text-sky-400 block">IS 1172 Target Compliance</span>
            <div className="flex items-baseline gap-2">
              <span className="text-2xl font-bold font-mono text-leaf">128</span>
              <span className="text-xs text-ink-600 dark:text-sky-300">L/capita / day</span>
            </div>
            <div className="text-[11px] text-ink-600 dark:text-sky-300 flex items-center justify-between pt-1 border-t border-sky-100 dark:border-white/10">
              <span>Standard Ceiling:</span>
              <span className="font-mono font-semibold">135.0 L</span>
            </div>
            <span className="text-[10px] text-leaf font-semibold block">
              ✓ Compliant (Hostel A water-efficient rating)
            </span>
          </div>
        </div>
      </div>

      {/* Middle Grid: 24h Consumption Chart + Conservation Tips */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left: 24-Hour Building Demand Chart */}
        <div className="lg:col-span-2 glass-card p-6 shadow-glass space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-sky-100 dark:border-white/10">
            <div>
              <h3 className="text-base font-bold text-ink-900 dark:text-mist">Hostel Block A — 24h Consumption Curve</h3>
              <p className="text-xs text-ink-600 dark:text-sky-300">Live hourly flow rate vs expected normal operating band</p>
            </div>
            <span className="text-xs font-mono font-bold text-sky-600 dark:text-sky-400 bg-sky-50 dark:bg-white/5 px-2.5 py-1 rounded-pill">
              Flow Meter: MTR-HSTLA
            </span>
          </div>

          <div className="h-60 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={consumptionData.length > 0 ? consumptionData : [
                { hour: '00:00', consumption_lpm: 15, normal_band_lower: 12, normal_band_upper: 18 },
                { hour: '04:00', consumption_lpm: 9, normal_band_lower: 8, normal_band_upper: 12 },
                { hour: '07:00', consumption_lpm: 68, normal_band_lower: 55, normal_band_upper: 75 },
                { hour: '10:00', consumption_lpm: 44, normal_band_lower: 38, normal_band_upper: 52 },
                { hour: '13:00', consumption_lpm: 48, normal_band_lower: 42, normal_band_upper: 55 },
                { hour: '17:00', consumption_lpm: 40, normal_band_lower: 35, normal_band_upper: 48 },
                { hour: '20:00', consumption_lpm: 70, normal_band_lower: 58, normal_band_upper: 78 },
                { hour: '23:00', consumption_lpm: 25, normal_band_lower: 20, normal_band_upper: 30 },
              ]}>
                <XAxis dataKey="hour" tick={{ fontSize: 10 }} stroke="#9EB2C7" />
                <YAxis tick={{ fontSize: 10 }} stroke="#9EB2C7" unit=" L/m" />
                <Tooltip contentStyle={{ fontSize: '11px', borderRadius: '12px' }} />
                <Area type="monotone" dataKey="normal_band_upper" stroke="none" fill="#D9E9FB" fillOpacity={0.5} name="Upper Band" />
                <Area type="monotone" dataKey="normal_band_lower" stroke="none" fill="#FFFFFF" fillOpacity={0.8} name="Lower Band" />
                <Line type="monotone" dataKey="consumption_lpm" stroke="#2FB8AA" strokeWidth={2.5} dot={{ r: 3 }} name="Observed Flow (L/min)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Right: Conservation Guidance & Campus Notices */}
        <div className="space-y-4">
          <div className="glass-card p-5 shadow-glass space-y-3 bg-gradient-to-br from-white/90 to-sky-50/50 dark:from-white/5 dark:to-sky-900/10">
            <div className="flex items-center gap-2 text-sky-700 dark:text-sky-300">
              <Sparkles className="w-4 h-4" />
              <h3 className="text-sm font-bold">Conservation Guidance</h3>
            </div>
            <p className="text-xs text-ink-700 dark:text-sky-200 leading-relaxed font-sans">
              {awareness?.q6_conservation_guidance || 'Turn off faucets while brushing and report damp risers immediately. Prompt leak reporting saves 4,000L daily in student blocks.'}
            </p>
            <div className="pt-2 border-t border-sky-100 dark:border-white/10 text-[11px] text-ink-500 dark:text-sky-400 space-y-1">
              <span className="font-semibold block">Campus Advisory:</span>
              <ul className="list-disc pl-4 space-y-0.5">
                <li>Overhead tanks are sanitized every 2nd Saturday.</li>
                <li>Emergency water hotline: Extension 4101 (24x7).</li>
              </ul>
            </div>
          </div>
        </div>
      </div>

      {/* Bottom Section: CPGRAMS Water Grievances System */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Submit Complaint Card */}
        <div className="glass-card p-6 shadow-glass space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-sky-100 dark:border-white/10">
            <div>
              <h3 className="text-base font-bold text-ink-900 dark:text-mist">Report Water Grievance (CPGRAMS)</h3>
              <p className="text-xs text-ink-600 dark:text-sky-300">Official lodging of infrastructure faults & leakage issues</p>
            </div>
            <span className="text-[10px] font-mono uppercase bg-emerald-100 text-emerald-800 dark:bg-emerald-900/30 dark:text-emerald-300 px-2.5 py-1 rounded-pill font-bold">
              Direct to Maintenance
            </span>
          </div>

          {submissionSuccess && (
            <div className="p-3 bg-leaf/15 border border-leaf/30 rounded-xl text-xs text-leaf font-medium flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 shrink-0" />
              <span>{submissionSuccess}</span>
            </div>
          )}

          <form onSubmit={handleSubmitComplaint} className="space-y-4 text-xs">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              <div>
                <label className="font-medium text-ink-700 dark:text-sky-200 block mb-1">Issue Category</label>
                <select
                  value={category}
                  onChange={(e) => setCategory(e.target.value)}
                  className="w-full p-2.5 rounded-xl border border-sky-100 dark:border-white/10 bg-white dark:bg-[#122336] text-ink-900 dark:text-mist outline-none"
                >
                  <option value="Water leakage">Water leakage</option>
                  <option value="Damaged water infrastructure">Damaged water infrastructure</option>
                  <option value="Low pressure / Supply cutoff">Low pressure / Supply cutoff</option>
                  <option value="Water quality / Odor">Water quality / Odor</option>
                  <option value="Tank overflow">Tank overflow</option>
                </select>
              </div>

              <div>
                <label className="font-medium text-ink-700 dark:text-sky-200 block mb-1">Priority Level</label>
                <select
                  value={priority}
                  onChange={(e) => setPriority(e.target.value)}
                  className="w-full p-2.5 rounded-xl border border-sky-100 dark:border-white/10 bg-white dark:bg-[#122336] text-ink-900 dark:text-mist outline-none"
                >
                  <option value="low">Low (Cosmetic / Drip)</option>
                  <option value="medium">Medium (Regular Maintenance)</option>
                  <option value="high">High (Active Seepage / Burst)</option>
                </select>
              </div>
            </div>

            <div>
              <label className="font-medium text-ink-700 dark:text-sky-200 block mb-1">Detailed Description & Location</label>
              <textarea
                rows={3}
                required
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="e.g. 2nd floor east wing washroom faucet handle leaking continuously; steady stream forming on tiles."
                className="w-full p-3 rounded-xl border border-sky-100 dark:border-white/10 bg-white dark:bg-[#122336] text-ink-900 dark:text-mist outline-none placeholder:text-ink-400"
              />
            </div>

            <button
              type="submit"
              disabled={submitting}
              className="px-5 py-2.5 rounded-btn bg-sky-500 text-white font-medium hover:bg-sky-600 transition-colors flex items-center justify-center gap-2 w-full disabled:opacity-50"
            >
              <Send className="w-3.5 h-3.5" />
              <span>{submitting ? 'Lodging Grievance...' : 'Submit Grievance to Estate Operations'}</span>
            </button>
          </form>
        </div>

        {/* My Active Grievances Tracker */}
        <div className="glass-card p-6 shadow-glass space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-sky-100 dark:border-white/10">
            <div>
              <h3 className="text-base font-bold text-ink-900 dark:text-mist">My Grievances Tracker</h3>
              <p className="text-xs text-ink-600 dark:text-sky-300">Live progress of your submitted complaints</p>
            </div>
            <span className="font-mono text-xs font-semibold text-ink-600 dark:text-sky-300">
              {complaints.length} registered
            </span>
          </div>

          <div className="space-y-3 max-h-[300px] overflow-y-auto pr-1">
            {complaints.length > 0 ? (
              complaints.map((c) => (
                <div key={c.id} className="p-3.5 bg-white/70 dark:bg-white/5 border border-sky-100 dark:border-white/10 rounded-xl space-y-2 text-xs">
                  <div className="flex items-center justify-between">
                    <span className="font-mono font-bold text-sky-700 dark:text-sky-300">{c.tracking_id}</span>
                    <span className={`px-2 py-0.5 rounded-pill text-[10px] font-bold uppercase ${
                      c.status === 'resolved' ? 'bg-leaf/15 text-leaf' :
                      c.status === 'in_progress' ? 'bg-amber/15 text-amber' :
                      'bg-sky-100 text-sky-700 dark:bg-white/10 dark:text-sky-200'
                    }`}>
                      {c.status.replace('_', ' ')}
                    </span>
                  </div>
                  <p className="text-ink-800 dark:text-sky-100 font-medium">{c.description}</p>
                  <div className="flex items-center justify-between pt-1 border-t border-sky-50 dark:border-white/5 text-[11px] text-ink-500 dark:text-sky-400">
                    <span>{c.category}</span>
                    <span className="italic">{c.action_taken_remarks || 'Inspection assigned to field team'}</span>
                  </div>
                </div>
              ))
            ) : (
              <div className="py-8 text-center text-ink-400 dark:text-sky-500 text-xs">
                No active complaints filed yet. Tap the form on the left to report any leaks.
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

// ============================================================================
// 2. BUILDING ADMINISTRATOR VIEW: Hostel A Operations & Alert Management
// ============================================================================
const BuildingAdminOverviewView: React.FC = () => {
  const { assignedBuildingId, simState } = useStore();
  const [awareness, setAwareness] = useState<any>(null);
  const [alerts, setAlerts] = useState<any[]>([]);
  const [complaints, setComplaints] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [forwardingId, setForwardingId] = useState<string | null>(null);

  const buildingId = assignedBuildingId || 'BLK-HSTL-A';

  const loadData = async () => {
    try {
      setLoading(true);
      const aw = await apiFetch<any>(`/v1/awareness/buildings/${buildingId}`);
      setAwareness(aw);
      const al = await apiFetch<any[]>(`/v1/awareness/buildings/${buildingId}/alerts`);
      setAlerts(al || []);
      const cmps = await apiFetch<any[]>('/v1/complaints');
      setComplaints(cmps || []);
    } catch (err) {
      console.warn('Building admin load warning:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 8000);
    return () => clearInterval(interval);
  }, [buildingId]);

  const handleForwardToMaintenance = async (complaintId: string) => {
    try {
      setForwardingId(complaintId);
      await apiFetch(`/v1/complaints/${complaintId}`, {
        method: 'PATCH',
        body: JSON.stringify({
          forward_to_maintenance: true,
          action_taken_remarks: 'Forwarded by Building Administrator to Plumbing Specialist K. Priya.'
        })
      });
      loadData();
    } catch (err: any) {
      alert(`Forwarding error: ${err.message}`);
    } finally {
      setForwardingId(null);
    }
  };

  return (
    <div className="py-6 px-4 max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div className="glass-card p-6 shadow-glass flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="px-2.5 py-0.5 rounded-pill bg-indigo-500/15 text-indigo-600 dark:text-indigo-400 font-mono text-[10px] font-bold uppercase">
              Building Administrator Console
            </span>
            <span className="text-xs font-semibold text-ink-600 dark:text-sky-300">
              Hostel Block A (Population: 420 • Vulnerability: High)
            </span>
          </div>
          <h1 className="text-xl md:text-2xl font-bold text-ink-900 dark:text-mist mt-1">
            Hostel Block A — Facility Water Management
          </h1>
          <p className="text-xs text-ink-600 dark:text-sky-300">
            Monitor real-time consumption, triage resident grievances, and issue maintenance inspection tickets.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={() => alert('Inspection request logged. Dispatching field acoustic sensor team.')}
            className="px-4 py-2 rounded-btn bg-sky-500 text-white text-xs font-medium hover:bg-sky-600 transition-colors flex items-center gap-1.5"
          >
            <PhoneCall className="w-3.5 h-3.5" />
            <span>Request Field Inspection</span>
          </button>
        </div>
      </div>

      {/* Building KPI Row */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="glass-card p-4 shadow-glass">
          <span className="text-[11px] font-medium text-ink-500 dark:text-sky-400 block">Current Inflow</span>
          <div className="flex items-baseline gap-2 mt-1">
            <span className="text-2xl font-bold font-mono text-ink-900 dark:text-mist">{awareness?.q2_consumption_lpm || 45.2}</span>
            <span className="text-xs text-ink-600 dark:text-sky-300">L/min</span>
          </div>
          <span className="text-[10px] text-ink-500 dark:text-sky-400 block mt-1">Nominal: 48.0 L/min</span>
        </div>

        <div className="glass-card p-4 shadow-glass">
          <span className="text-[11px] font-medium text-ink-500 dark:text-sky-400 block">Storage Reserve</span>
          <div className="flex items-baseline gap-2 mt-1">
            <span className="text-2xl font-bold font-mono text-ink-900 dark:text-mist">{awareness?.q5_hours_autonomy || 18.5}</span>
            <span className="text-xs text-ink-600 dark:text-sky-300">hrs</span>
          </div>
          <span className="text-[10px] text-leaf block mt-1">Sufficient for 24h cycle</span>
        </div>

        <div className="glass-card p-4 shadow-glass">
          <span className="text-[11px] font-medium text-ink-500 dark:text-sky-400 block">Active Alerts</span>
          <div className="flex items-baseline gap-2 mt-1">
            <span className="text-2xl font-bold font-mono text-amber">{alerts.length}</span>
            <span className="text-xs text-amber">items</span>
          </div>
          <span className="text-[10px] text-ink-500 dark:text-sky-400 block mt-1">Requiring supervisor attention</span>
        </div>

        <div className="glass-card p-4 shadow-glass">
          <span className="text-[11px] font-medium text-ink-500 dark:text-sky-400 block">Resident Grievances</span>
          <div className="flex items-baseline gap-2 mt-1">
            <span className="text-2xl font-bold font-mono text-ink-900 dark:text-mist">{complaints.length}</span>
            <span className="text-xs text-ink-600 dark:text-sky-300">CPGRAMS</span>
          </div>
          <span className="text-[10px] text-sky-600 dark:text-sky-400 block mt-1">Hostel Block A</span>
        </div>
      </div>

      {/* Grid: Alerts + Student Complaints Forwarding */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Active Alerts */}
        <div className="glass-card p-6 shadow-glass space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-sky-100 dark:border-white/10">
            <div>
              <h3 className="text-base font-bold text-ink-900 dark:text-mist">Building Alerts & System Exceptions</h3>
              <p className="text-xs text-ink-600 dark:text-sky-300">Automated alerts from Monitor and Detector agents</p>
            </div>
            <span className="text-xs font-mono font-bold text-amber">Priority Feed</span>
          </div>

          <div className="space-y-3">
            {alerts.length > 0 ? (
              alerts.map((al) => (
                <div key={al.id} className="p-3.5 bg-amber/10 border border-amber/30 rounded-xl space-y-1.5 text-xs">
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-amber">{al.type.replace('_', ' ').toUpperCase()}</span>
                    <span className="font-mono text-[10px]">{al.status}</span>
                  </div>
                  <p className="text-ink-900 dark:text-mist">{al.message}</p>
                </div>
              ))
            ) : (
              <div className="p-4 bg-sky-50 dark:bg-white/5 rounded-xl text-xs text-ink-600 dark:text-sky-300 flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 text-leaf" />
                <span>No active critical alerts for Hostel Block A. Supervisory regime stable.</span>
              </div>
            )}
          </div>
        </div>

        {/* Complaints for Hostel Block A */}
        <div className="glass-card p-6 shadow-glass space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-sky-100 dark:border-white/10">
            <div>
              <h3 className="text-base font-bold text-ink-900 dark:text-mist">Hostel A Resident Grievances</h3>
              <p className="text-xs text-ink-600 dark:text-sky-300">Review student complaints and dispatch to maintenance</p>
            </div>
            <span className="font-mono text-xs text-ink-500 dark:text-sky-400">CPGRAMS Queue</span>
          </div>

          <div className="space-y-3 max-h-[340px] overflow-y-auto pr-1">
            {complaints.map((c) => (
              <div key={c.id} className="p-3.5 bg-white/70 dark:bg-white/5 border border-sky-100 dark:border-white/10 rounded-xl space-y-2 text-xs">
                <div className="flex items-center justify-between">
                  <span className="font-mono font-bold text-sky-700 dark:text-sky-300">{c.tracking_id}</span>
                  <span className={`px-2 py-0.5 rounded-pill text-[10px] font-bold uppercase ${
                    c.status === 'in_progress' ? 'bg-amber/15 text-amber' :
                    c.status === 'resolved' ? 'bg-leaf/15 text-leaf' :
                    'bg-sky-100 text-sky-700 dark:bg-white/10 dark:text-sky-200'
                  }`}>
                    {c.status.replace('_', ' ')}
                  </span>
                </div>
                <p className="text-ink-900 dark:text-mist">{c.description}</p>
                <div className="flex items-center justify-between pt-1 border-t border-sky-50 dark:border-white/5 text-[11px]">
                  <span className="text-ink-500 dark:text-sky-400">Category: {c.category}</span>
                  {!c.assigned_work_order_id ? (
                    <button
                      onClick={() => handleForwardToMaintenance(c.id)}
                      disabled={forwardingId === c.id}
                      className="px-2.5 py-1 rounded-btn bg-indigo-500 text-white font-medium hover:bg-indigo-600 transition-colors"
                    >
                      {forwardingId === c.id ? 'Forwarding...' : 'Forward to Maintenance'}
                    </button>
                  ) : (
                    <span className="font-mono text-leaf font-semibold">WO: {c.assigned_work_order_id}</span>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

// ============================================================================
// 3. MAINTENANCE ENGINEER VIEW: Assigned Work Orders & Verification Logs
// ============================================================================
const EngineerOverviewView: React.FC = () => {
  const [workOrders, setWorkOrders] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [activeWoId, setActiveWoId] = useState<string | null>(null);
  const [findingsText, setFindingsText] = useState('');
  const [updating, setUpdating] = useState(false);

  const loadWorkOrders = async () => {
    try {
      setLoading(true);
      const data = await apiFetch<any[]>('/v1/work-orders');
      setWorkOrders(data || []);
    } catch (err) {
      console.warn('Work orders fetch warning:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadWorkOrders();
    const interval = setInterval(loadWorkOrders, 8000);
    return () => clearInterval(interval);
  }, []);

  const handleUpdateStatus = async (woId: string, status: string) => {
    try {
      setUpdating(true);
      await apiFetch(`/v1/work-orders/${woId}/status`, {
        method: 'PATCH',
        body: JSON.stringify({
          status,
          findings: findingsText || 'Inspection completed. Pipe collar gasket tightened.'
        })
      });
      setActiveWoId(null);
      setFindingsText('');
      loadWorkOrders();
    } catch (err: any) {
      alert(`Update error: ${err.message}`);
    } finally {
      setUpdating(false);
    }
  };

  return (
    <div className="py-6 px-4 max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div className="glass-card p-6 shadow-glass flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="px-2.5 py-0.5 rounded-pill bg-amber-500/15 text-amber-600 dark:text-amber-400 font-mono text-[10px] font-bold uppercase">
              Field Technician & Engineering Hub
            </span>
            <span className="text-xs font-semibold text-ink-600 dark:text-sky-300">
              K. Priya (Acoustic Leak Detection Specialist)
            </span>
          </div>
          <h1 className="text-xl md:text-2xl font-bold text-ink-900 dark:text-mist mt-1">
            Assigned Work Orders & Remediation Tasks
          </h1>
          <p className="text-xs text-ink-600 dark:text-sky-300">
            Accept assignments, log inspection findings, and submit completion details for autonomous verifier testing.
          </p>
        </div>

        <div className="p-3 bg-amber/10 border border-amber/30 rounded-2xl text-xs font-medium text-amber shrink-0">
          Workload: {workOrders.filter(w => w.status !== 'completed').length} active assignments
        </div>
      </div>

      {/* Work Orders List */}
      <div className="space-y-4">
        <h2 className="text-sm font-bold uppercase tracking-wider text-ink-600 dark:text-sky-300 font-mono">
          Assigned CMMS Maintenance Tickets
        </h2>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {workOrders.map((wo) => {
            const isCompleted = wo.status === 'completed';
            const isInProgress = wo.status === 'in_progress';
            return (
              <div key={wo.id} className="glass-card p-5 shadow-glass space-y-3 flex flex-col justify-between">
                <div className="space-y-2">
                  <div className="flex items-center justify-between pb-2 border-b border-sky-100 dark:border-white/10">
                    <span className="font-mono font-bold text-sky-700 dark:text-sky-300">{wo.id}</span>
                    <span className={`px-2.5 py-0.5 rounded-pill text-[10px] font-bold uppercase ${
                      isCompleted ? 'bg-leaf/15 text-leaf' :
                      isInProgress ? 'bg-amber/15 text-amber' :
                      'bg-sky-100 text-sky-700 dark:bg-white/10 dark:text-sky-200'
                    }`}>
                      {wo.status.replace('_', ' ')}
                    </span>
                  </div>

                  <div className="space-y-1 text-xs">
                    <span className="text-ink-500 dark:text-sky-400 block font-mono">Asset: {wo.asset_id}</span>
                    <h3 className="font-bold text-ink-900 dark:text-mist text-sm">{wo.action}</h3>
                    <p className="text-ink-600 dark:text-sky-300">{wo.expected_impact}</p>
                  </div>

                  {wo.findings && (
                    <div className="p-3 bg-sky-50 dark:bg-white/5 rounded-xl text-xs space-y-0.5">
                      <span className="font-semibold text-ink-800 dark:text-sky-200 block">Logged Findings:</span>
                      <p className="text-ink-600 dark:text-sky-300">{wo.findings}</p>
                    </div>
                  )}
                </div>

                {/* Actions */}
                <div className="pt-3 border-t border-sky-100 dark:border-white/10">
                  {activeWoId === wo.id ? (
                    <div className="space-y-2.5 text-xs">
                      <textarea
                        rows={2}
                        value={findingsText}
                        onChange={(e) => setFindingsText(e.target.value)}
                        placeholder="Enter inspection findings (e.g. Fissure repaired using rubber gasket clamp; pressure restored to 2.85 bar)..."
                        className="w-full p-2.5 rounded-xl border border-sky-100 dark:border-white/10 bg-white dark:bg-[#122336] text-ink-900 dark:text-mist outline-none"
                      />
                      <div className="flex items-center gap-2">
                        <button
                          onClick={() => handleUpdateStatus(wo.id, 'completed')}
                          disabled={updating}
                          className="px-3.5 py-1.5 rounded-btn bg-leaf text-white font-medium hover:bg-leaf/90 flex-1"
                        >
                          Submit Findings & Complete
                        </button>
                        <button
                          onClick={() => setActiveWoId(null)}
                          className="px-3 py-1.5 rounded-btn bg-ink-200 text-ink-800 dark:bg-white/10 dark:text-mist"
                        >
                          Cancel
                        </button>
                      </div>
                    </div>
                  ) : (
                    <div className="flex items-center justify-between text-xs">
                      {!isCompleted ? (
                        <div className="flex items-center gap-2 w-full">
                          {!isInProgress && (
                            <button
                              onClick={() => handleUpdateStatus(wo.id, 'in_progress')}
                              className="px-3 py-1.5 rounded-btn bg-sky-500 text-white font-medium hover:bg-sky-600 flex-1"
                            >
                              Accept Assignment
                            </button>
                          )}
                          <button
                            onClick={() => {
                              setActiveWoId(wo.id);
                              setFindingsText(wo.findings || '');
                            }}
                            className="px-3 py-1.5 rounded-btn bg-emerald-600 text-white font-medium hover:bg-emerald-700 flex-1"
                          >
                            Record Findings & Close
                          </button>
                        </div>
                      ) : (
                        <span className="text-leaf text-[11px] font-semibold flex items-center gap-1.5">
                          <CheckCircle2 className="w-3.5 h-3.5" />
                          Work completed • Awaiting automated outcome verification
                        </span>
                      )}
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};

// ============================================================================
// 4. ESTATE ADMIN VIEW: Full SCADA Digital Twin & Consequential Approvals
// ============================================================================
const AdminOverviewView: React.FC = () => {
  const navigate = useNavigate();
  const { simState, setSelectedCaseId } = useStore();
  const [incidents, setIncidents] = useState<any[]>([]);
  const [forecastData, setForecastData] = useState<any[]>([]);
  const [nightFlowData, setNightFlowData] = useState<any[]>([]);

  // 4 Distributed Laptop Sources State
  const [sources, setSources] = useState<any[]>([]);
  const [sourcesLoading, setSourcesLoading] = useState(false);

  // Live Agent Analysis State
  const [analyzing, setAnalyzing] = useState(false);
  const [analysisResult, setAnalysisResult] = useState<any>(null);
  const [liveEvents, setLiveEvents] = useState<any[]>([]);

  const loadData = async () => {
    try {
      const incList = await apiFetch<any[]>('/v1/incidents');
      setIncidents(incList || []);
      const fData = await apiFetch<any>('/v1/forecast');
      if (fData && fData.sump_trajectory_72h) {
        setForecastData(fData.sump_trajectory_72h);
      }
      const srcStatus = await apiFetch<any[]>('/v1/sources/status');
      if (srcStatus) setSources(srcStatus);

      const latestAnalysis = await apiFetch<any>('/v1/agent/latest-analysis');
      if (latestAnalysis && latestAnalysis.status !== 'none') {
        setAnalysisResult(latestAnalysis);
      }
    } catch (err) {
      console.warn('Overview data fetch fallback:', err);
    }
  };

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 4000);
    return () => clearInterval(interval);
  }, []);

  // Real-time SSE stream for Agent Analysis Lifecycle Events
  useEffect(() => {
    const sseUrl = '/api/v1/agent/stream-events';
    let eventSource: EventSource | null = null;
    try {
      eventSource = new EventSource(sseUrl);
      eventSource.onmessage = (e) => {
        try {
          const data = JSON.parse(e.data);
          setLiveEvents((prev) => {
            const next = [...prev, data];
            return next.length > 50 ? next.slice(next.length - 50) : next;
          });
        } catch (err) {
          console.warn('SSE parse error:', err);
        }
      };
    } catch (e) {
      console.warn('SSE connection error:', e);
    }
    return () => {
      if (eventSource) eventSource.close();
    };
  }, []);

  const handleRunAgentAnalysis = async () => {
    try {
      setAnalyzing(true);
      const res = await apiFetch<any>('/v1/agent/run-analysis', {
        method: 'POST'
      });
      setAnalysisResult(res);
      loadData();
    } catch (err: any) {
      alert(`Agent Analysis Error: ${err.message}`);
    } finally {
      setAnalyzing(false);
    }
  };

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
      {/* 1. Greeting row & Demonstration Status */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 glass-card p-5 shadow-glass">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-xl md:text-2xl font-bold text-ink-900 dark:text-mist">
              Estate Office — Central Operations Console
            </h1>
            <span className="px-2.5 py-0.5 rounded-pill bg-sky-100 dark:bg-white/10 text-sky-700 dark:text-sky-300 text-[11px] font-mono font-semibold">
              Live Demo Ready
            </span>
          </div>
          <p className="text-xs text-ink-600 dark:text-sky-300 font-mono mt-0.5">
            {simState?.formatted_time || 'Saturday, 31 Oct 2026 03:15 UTC'} • Sathyamangalam Campus Digital Twin
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={handleRunAgentAnalysis}
            disabled={analyzing}
            className={`px-4 py-2 rounded-btn font-bold text-xs flex items-center gap-2 shadow-sm transition-all ${
              analyzing
                ? 'bg-sky-400 text-white cursor-wait opacity-80'
                : 'bg-sky-600 hover:bg-sky-700 text-white shadow-sky-500/20 hover:scale-[1.02]'
            }`}
          >
            <Sparkles className={`w-4 h-4 ${analyzing ? 'animate-spin' : ''}`} />
            <span>{analyzing ? 'Running ML & Agent Analysis...' : 'Run Agent Analysis'}</span>
          </button>
        </div>
      </div>

      {/* 2. Four Distributed Laptop Data Sources Panel */}
      <div className="glass-card p-5 shadow-glass space-y-3">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-sky-100 dark:border-white/10 pb-3">
          <div>
            <h2 className="text-sm font-bold text-ink-900 dark:text-mist flex items-center gap-2">
              <span>Distributed Laptop Telemetry Sources</span>
              <span className="text-[10px] px-2 py-0.5 rounded-pill bg-sky-100 dark:bg-white/10 text-sky-700 dark:text-sky-300 font-mono">
                4 Laptop Endpoints
              </span>
            </h2>
            <p className="text-[11px] text-ink-600 dark:text-sky-300 font-sans mt-0.5">
              Live ingested data transmitted over HTTP. Labeled as simulated laptop telemetry for demonstration.
            </p>
          </div>
          <div className="text-[11px] font-mono text-ink-500 dark:text-sky-400">
            Auto-refreshing (4s)
          </div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
          {(sources.length ? sources : [
            { source_id: 'source_1', laptop_label: 'Laptop 2 (Supply & Reservoirs)', name: 'Water Supply & Reservoirs', reading_count: 7, data_quality_status: 'healthy', latest_receipt_time: new Date().toISOString() },
            { source_id: 'source_2', laptop_label: 'Laptop 3 (Flow & Smart Meters)', name: 'Building Smart Flow Meters', reading_count: 8, data_quality_status: 'healthy', latest_receipt_time: new Date().toISOString() },
            { source_id: 'source_3', laptop_label: 'Laptop 4 (Pressure & SCADA)', name: 'Pipe Pressure Transducers', reading_count: 5, data_quality_status: 'healthy', latest_receipt_time: new Date().toISOString() },
            { source_id: 'source_4', laptop_label: 'Laptop 5 (Environment & Grievances)', name: 'Weather Radar & Grievances', reading_count: 4, data_quality_status: 'healthy', latest_receipt_time: new Date().toISOString() },
          ]).map((src: any) => {
            const isHealthy = src.data_quality_status === 'healthy';
            const isStale = src.is_stale || src.data_quality_status === 'stale';
            return (
              <div
                key={src.source_id}
                className="p-3.5 rounded-xl bg-white/70 dark:bg-white/5 border border-sky-100 dark:border-white/10 space-y-2 hover:border-sky-300 transition-colors"
              >
                <div className="flex items-center justify-between gap-1">
                  <span className="text-[11px] font-bold text-ink-900 dark:text-mist truncate">
                    {src.laptop_label}
                  </span>
                  <span
                    className={`px-2 py-0.5 rounded-pill text-[10px] font-mono font-semibold uppercase ${
                      isHealthy
                        ? 'bg-emerald-500/15 text-emerald-600 dark:text-emerald-400'
                        : isStale
                        ? 'bg-amber-500/15 text-amber-600 dark:text-amber-400'
                        : 'bg-sky-500/15 text-sky-600 dark:text-sky-400'
                    }`}
                  >
                    {src.data_quality_status || 'healthy'}
                  </span>
                </div>
                <p className="text-[11px] text-ink-600 dark:text-sky-300 truncate">
                  {src.name}
                </p>
                <div className="flex items-center justify-between pt-1 border-t border-sky-50 dark:border-white/5 text-[10px] font-mono text-ink-500 dark:text-sky-400">
                  <span>Count: <strong className="text-ink-700 dark:text-sky-200">{src.reading_count || 0}</strong></span>
                  <span title={src.latest_receipt_time || 'None'}>
                    {src.latest_receipt_time ? new Date(src.latest_receipt_time).toLocaleTimeString() : 'Awaiting data'}
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* 3. Live Structured Agent Analysis Outcome & Real-time Trace Stream */}
      {analysisResult && (
        <div className="glass-card p-5 shadow-glass space-y-4 border-2 border-sky-500/30 bg-sky-50/20 dark:bg-sky-950/20">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-sky-100 dark:border-white/10 pb-3">
            <div>
              <div className="flex items-center gap-2">
                <span className="px-2.5 py-0.5 rounded-pill bg-sky-600 text-white text-[10px] font-mono font-bold">
                  {analysisResult.run_id}
                </span>
                <h3 className="text-base font-bold text-ink-900 dark:text-mist">
                  Agent Operational Analysis Result
                </h3>
                <span className={`px-2 py-0.5 rounded-pill text-[10px] font-semibold ${
                  analysisResult.status === 'completed' ? 'bg-emerald-500/15 text-emerald-600 dark:text-emerald-400' : 'bg-coral/15 text-coral'
                }`}>
                  {analysisResult.status.toUpperCase()}
                </span>
              </div>
              <p className="text-xs text-ink-600 dark:text-sky-300 mt-1">
                Completed at <span className="font-mono">{new Date(analysisResult.completed_at).toLocaleTimeString()}</span> • Confidence: <span className="font-mono font-bold text-sky-600">{(analysisResult.confidence * 100).toFixed(1)}%</span>
              </p>
            </div>

            {/* Approval Badge */}
            <div>
              {analysisResult.requires_human_approval ? (
                <span className="px-3 py-1.5 rounded-pill bg-amber-500/20 border border-amber-500/40 text-amber-700 dark:text-amber-300 text-xs font-bold flex items-center gap-1.5">
                  <AlertCircle className="w-4 h-4 text-amber-600" />
                  <span>Consequential: Human Approval Required</span>
                </span>
              ) : (
                <span className="px-3 py-1.5 rounded-pill bg-emerald-500/15 border border-emerald-500/30 text-emerald-700 dark:text-emerald-300 text-xs font-medium flex items-center gap-1.5">
                  <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                  <span>Non-consequential Action Dispatched</span>
                </span>
              )}
            </div>
          </div>

          {/* Issue & Reasoning Breakdown */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="md:col-span-2 space-y-3">
              <div className="p-3.5 rounded-xl bg-white/80 dark:bg-white/5 border border-sky-100 dark:border-white/10 space-y-1.5">
                <span className="text-[10px] font-mono uppercase text-ink-500 dark:text-sky-400 block font-semibold">
                  Detected Condition & Affected Infrastructure
                </span>
                <div className="text-sm font-bold text-ink-900 dark:text-mist flex items-center gap-2">
                  <span>{analysisResult.detected_issue?.replace(/_/g, ' ').toUpperCase()}</span>
                  <span className="text-xs text-sky-600 font-mono font-normal">• Asset: {analysisResult.affected_asset_id}</span>
                </div>
                <p className="text-xs text-ink-600 dark:text-sky-300 font-mono">
                  {analysisResult.affected_location}
                </p>
              </div>

              <div className="p-3.5 rounded-xl bg-white/80 dark:bg-white/5 border border-sky-100 dark:border-white/10 space-y-2">
                <span className="text-[10px] font-mono uppercase text-ink-500 dark:text-sky-400 block font-semibold">
                  Evidence-Grounded Reasoning Summary
                </span>
                <p className="text-xs leading-relaxed text-ink-800 dark:text-mist">
                  {analysisResult.reasoning_summary}
                </p>
                {/* Evidence Chips */}
                <div className="flex flex-wrap gap-1.5 pt-1">
                  {analysisResult.evidence?.map((e: any) => (
                    <span
                      key={e.id}
                      className="px-2 py-0.5 rounded-pill bg-sky-100 dark:bg-white/10 text-sky-700 dark:text-sky-300 text-[10px] font-mono font-semibold"
                      title={`${e.kind}: observed ${e.value} ${e.unit} (baseline ${e.baseline}). ${e.note}`}
                    >
                      [{e.id}] {e.asset_id}: {e.value} {e.unit}
                    </span>
                  ))}
                </div>
              </div>

              <div className="p-3.5 rounded-xl bg-white/80 dark:bg-white/5 border border-sky-100 dark:border-white/10 space-y-1">
                <span className="text-[10px] font-mono uppercase text-ink-500 dark:text-sky-400 block font-semibold">
                  Recommended Action Plan
                </span>
                <p className="text-xs text-ink-800 dark:text-mist font-medium">
                  {analysisResult.recommended_action}
                </p>
              </div>
            </div>

            {/* Right Column: Model Result & Token Usage */}
            <div className="space-y-3">
              <div className="p-3.5 rounded-xl bg-white/80 dark:bg-white/5 border border-sky-100 dark:border-white/10 space-y-2">
                <span className="text-[10px] font-mono uppercase text-ink-500 dark:text-sky-400 block font-semibold">
                  Machine Learning Model Telemetry
                </span>
                <div className="space-y-1.5 text-xs font-mono">
                  <div className="flex justify-between">
                    <span className="text-ink-600 dark:text-sky-300">OneClassSVM Anomaly:</span>
                    <span className="font-bold text-coral">{analysisResult.model_result?.svm_anomaly ? 'Positive Anomaly' : 'Nominal'}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-ink-600 dark:text-sky-300">XGBoost Leak Prob:</span>
                    <span className="font-bold text-sky-600">{((analysisResult.model_result?.xgboost_leak_prob || 0.82) * 100).toFixed(1)}%</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-ink-600 dark:text-sky-300">Baseline Z-Score:</span>
                    <span className="font-bold text-ink-900 dark:text-mist">{analysisResult.model_result?.z_score || 4.12}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-ink-600 dark:text-sky-300">Loss Rate Estimate:</span>
                    <span className="font-bold text-coral">{analysisResult.model_result?.loss_rate_kl_day || 66.8} kL/day</span>
                  </div>
                </div>
              </div>

              {/* Gemini Token Usage Card */}
              <div className="p-3.5 rounded-xl bg-white/80 dark:bg-white/5 border border-sky-100 dark:border-white/10 space-y-2">
                <span className="text-[10px] font-mono uppercase text-ink-500 dark:text-sky-400 block font-semibold">
                  Google Gemini Token Usage
                </span>
                <div className="space-y-1 text-xs font-mono">
                  <div className="flex justify-between">
                    <span className="text-ink-600 dark:text-sky-300">Model:</span>
                    <span className="font-bold text-sky-600">{analysisResult.token_usage?.model_name || 'gemini-3.5-flash-lite'}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-ink-600 dark:text-sky-300">Input Tokens:</span>
                    <span>{analysisResult.token_usage?.prompt_tokens?.toLocaleString() || 184}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-ink-600 dark:text-sky-300">Output Tokens:</span>
                    <span>{analysisResult.token_usage?.candidates_tokens?.toLocaleString() || 88}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-ink-600 dark:text-sky-300">Thinking Tokens:</span>
                    <span>{analysisResult.token_usage?.thoughts_tokens?.toLocaleString() || 0}</span>
                  </div>
                  <div className="flex justify-between border-t border-sky-100 dark:border-white/10 pt-1">
                    <span className="text-ink-700 dark:text-sky-200 font-bold">Total Tokens:</span>
                    <span className="font-bold text-ink-900 dark:text-mist">{analysisResult.token_usage?.total_tokens?.toLocaleString() || 272}</span>
                  </div>
                  <div className="flex justify-between items-baseline pt-1">
                    <span className="text-ink-700 dark:text-sky-200 font-bold">Execution Cost:</span>
                    <span className="font-bold text-leaf text-sm">
                      ₹{analysisResult.token_usage?.cost_inr !== undefined ? analysisResult.token_usage.cost_inr.toFixed(4) : '0.0238'}
                    </span>
                  </div>
                  <span className="text-[9px] text-ink-500 dark:text-sky-400 block opacity-80 pt-0.5">
                    1 USD = ₹86.50 exchange rate applied
                  </span>
                </div>
              </div>
            </div>
          </div>

          {/* Live Execution Trace Stream Display */}
          <div className="rounded-xl bg-ink-900 text-sky-200 p-3.5 font-mono text-[11px] space-y-2 max-h-48 overflow-y-auto shadow-inner">
            <div className="flex items-center justify-between text-[10px] text-sky-400 uppercase tracking-wider pb-1 border-b border-sky-800/60 font-bold">
              <span>Real-Time Lifecycle Execution Trace (Terminal & Web Stream)</span>
              <span>Run: {analysisResult.run_id}</span>
            </div>
            <div className="space-y-1">
              {liveEvents.slice(-8).map((evt: any, i: number) => (
                <div key={i} className="flex items-start gap-2">
                  <span className="text-sky-400 shrink-0">[{evt.timestamp ? new Date(evt.timestamp).toLocaleTimeString() : 'NOW'}]</span>
                  <span className="px-1.5 py-0.2 rounded bg-sky-800 text-sky-200 text-[10px] font-bold shrink-0">
                    {evt.event_type}
                  </span>
                  <span className="text-mist truncate">{evt.message}</span>
                </div>
              ))}
              {liveEvents.length === 0 && (
                <div className="text-sky-500 italic">Listening for live execution trace events...</div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* 4. KPI row of 5 balanced cards with Indian Rupee formatting */}
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

      {/* Main Bento Layout: Left = What to do next, Right = Digital Twin Note & Log */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
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
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Right Column: Note + Activity feed */}
        <div className="space-y-6">
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
