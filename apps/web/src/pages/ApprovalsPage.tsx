import React, { useEffect, useState } from 'react';
import { Check, X, ShieldAlert, AlertTriangle, ArrowRight, CheckCircle2, RefreshCw } from 'lucide-react';
import { apiFetch } from '../api';
import { useStore } from '../store/useStore';

export const ApprovalsPage: React.FC = () => {
  const { role } = useStore();
  const [approvals, setApprovals] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [note, setNote] = useState('');

  const loadApprovals = async () => {
    try {
      setLoading(true);
      const data = await apiFetch<any[]>('/v1/approvals');
      setApprovals(data || []);
    } catch (err) {
      console.warn('Approvals fetch fallback:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadApprovals();
  }, []);

  const handleDecision = async (id: string, decision: 'approved' | 'rejected') => {
    if (role !== 'admin') {
      alert('Forbidden: Only Estate Admin can approve or reject consequential actions.');
      return;
    }
    try {
      await apiFetch(`/v1/approvals/${id}`, {
        method: 'POST',
        body: JSON.stringify({ decision, note: note || `Decision ${decision} recorded by Estate Admin.` }),
      });
      setNote('');
      loadApprovals();
    } catch (err: any) {
      alert(`Approval error: ${err.message}`);
    }
  };

  return (
    <div className="py-6 px-4 max-w-6xl mx-auto space-y-6">
      {/* Header */}
      <div className="glass-card p-6 shadow-glass flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <span className="text-[11px] font-mono text-sky-500 uppercase font-semibold">TCS Capability 6</span>
          <h1 className="text-2xl font-bold text-ink-900 dark:text-mist">Human Control & Approvals Center</h1>
          <p className="text-xs text-ink-600 dark:text-sky-300 mt-1">
            Consequential actions affecting supply, pumps, or vulnerable blocks require explicit Estate Admin sign-off.
          </p>
        </div>
        <div className="flex items-center gap-2">
          {role === 'admin' ? (
            <span className="px-3 py-1.5 rounded-pill bg-sky-500 text-white text-xs font-semibold shadow-sm">
              Authorized: Estate Admin
            </span>
          ) : (
            <span className="px-3 py-1.5 rounded-pill bg-amber/15 text-amber text-xs font-semibold">
              Viewer Mode (Read-only)
            </span>
          )}
        </div>
      </div>

      {/* Approvals List */}
      <div className="space-y-4">
        {approvals.length === 0 ? (
          <div className="glass-card p-12 text-center text-xs text-ink-600 dark:text-sky-300 space-y-2">
            <CheckCircle2 className="w-8 h-8 text-leaf mx-auto" />
            <p className="font-semibold text-sm text-ink-900 dark:text-mist">No Pending Approvals</p>
            <p>All scheduled water operations and maintenance orders are in compliance with campus equity rules.</p>
          </div>
        ) : (
          approvals.map((app) => (
            <div
              key={app.id}
              className="glass-card p-6 shadow-glass space-y-4 border border-sky-100 dark:border-white/10"
            >
              <div className="flex flex-col md:flex-row md:items-center justify-between gap-2 pb-3 border-b border-sky-100 dark:border-white/10">
                <div className="flex items-center gap-2.5">
                  <span className={`px-2.5 py-1 rounded-pill text-xs font-bold ${
                    app.status === 'pending' ? 'bg-amber/15 text-amber' : (app.status === 'approved' ? 'bg-leaf/15 text-leaf' : 'bg-coral/15 text-coral')
                  }`}>
                    {app.status.toUpperCase()}
                  </span>
                  <h3 className="font-bold text-sm text-ink-900 dark:text-mist">{app.title}</h3>
                </div>
                <span className="text-xs font-mono text-ink-600 dark:text-sky-300">{app.id}</span>
              </div>

              <p className="text-xs text-ink-900 dark:text-mist leading-relaxed">
                {app.description}
              </p>

              {/* Equity & Vulnerability Flag */}
              {app.vulnerable_flag && (
                <div className="p-3.5 rounded-xl bg-amber/10 border border-amber/30 space-y-1 text-xs">
                  <div className="flex items-center gap-1.5 text-amber font-bold">
                    <ShieldAlert className="w-4 h-4" />
                    <span>Vulnerable Block Protection Active:</span>
                  </div>
                  <p className="text-ink-600 dark:text-sky-300">
                    {app.equity_check || 'Guaranteed 85% potable water baseline constraint strictly held for all residents.'}
                  </p>
                </div>
              )}

              {/* Rollback Procedure */}
              <div className="p-3 rounded-xl bg-sky-50/70 dark:bg-white/5 text-xs text-ink-600 dark:text-sky-300">
                <span className="font-semibold text-ink-900 dark:text-mist block">Rollback Step:</span>
                Valve returns to 100% open and transfer pump reverts to continuous state if header pressure drops below 1.8 bar.
              </div>

              {/* Decision Actions for Admin */}
              {app.status === 'pending' && (
                <div className="pt-2 flex flex-col md:flex-row items-stretch md:items-center justify-between gap-4">
                  <input
                    type="text"
                    value={note}
                    onChange={(e) => setNote(e.target.value)}
                    placeholder="Enter approval or rejection reason..."
                    className="flex-1 px-4 py-2 rounded-btn glass-panel border border-sky-200 dark:border-white/10 text-xs text-ink-900 dark:text-mist outline-none focus:border-sky-500"
                  />

                  {role === 'admin' ? (
                    <div className="flex items-center gap-2">
                      <button
                        onClick={() => handleDecision(app.id, 'approved')}
                        className="px-5 py-2 rounded-btn bg-leaf text-white text-xs font-semibold flex items-center gap-1.5 shadow-sm hover:opacity-90 transition-opacity"
                      >
                        <Check className="w-3.5 h-3.5" />
                        <span>Approve action</span>
                      </button>
                      <button
                        onClick={() => handleDecision(app.id, 'rejected')}
                        className="px-5 py-2 rounded-btn bg-coral text-white text-xs font-semibold flex items-center gap-1.5 shadow-sm hover:opacity-90 transition-opacity"
                      >
                        <X className="w-3.5 h-3.5" />
                        <span>Reject action</span>
                      </button>
                    </div>
                  ) : (
                    <span className="text-xs text-amber font-medium italic">
                      Viewers cannot sign off on consequential interventions.
                    </span>
                  )}
                </div>
              )}

              {app.status !== 'pending' && (
                <div className="pt-2 text-xs font-mono text-ink-600 dark:text-sky-300">
                  Decision by: {app.decision_by || 'Estate Admin'} • Note: {app.decision_note || 'Logged to audit trail'}
                </div>
              )}
            </div>
          ))
        )}
      </div>
    </div>
  );
};
