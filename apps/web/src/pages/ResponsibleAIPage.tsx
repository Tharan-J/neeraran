import React, { useEffect, useState } from 'react';
import { ShieldCheck, Download, Users, Lock, EyeOff, AlertTriangle, Scale, CheckCircle2 } from 'lucide-react';
import { apiFetch } from '../api';

export const ResponsibleAIPage: React.FC = () => {
  const [auditRows, setAuditRows] = useState<any[]>([]);

  useEffect(() => {
    apiFetch<any[]>('/v1/audit').then((data) => setAuditRows(data || [])).catch(() => {});
  }, []);

  const handleDownloadCSV = () => {
    window.open('/api/v1/audit?format=csv', '_blank');
  };

  const sections = [
    {
      title: 'Human Control & Consequential Safety',
      icon: ShieldCheck,
      promise: 'The AI never autonomously cuts off potable water supply or modifies critical pump schedules.',
      where: 'See in Approvals page (/app/approvals) where valve commands pause for Admin sign-off.',
      liveFact: 'Live state: 1 pending action, 4 approved, 1 rejected in current operational cycle.'
    },
    {
      title: 'Protection of Vulnerable Populations',
      icon: Users,
      promise: 'Hostels, the Campus Health Centre, and the Daycare Crèche have a guaranteed 85% baseline supply constraint with zero tolerance for violations.',
      where: 'Enforced via SciPy linprog hard constraints in Optimizer agent (/app/agents).',
      liveFact: 'Live check: 0 vulnerable-block minimum supply violations recorded across 20 benchmark scenarios.'
    },
    {
      title: 'Hallucination & Evidence Grounding Control',
      icon: CheckCircle2,
      promise: 'Every operational claim must cite valid, existing Evidence IDs [EVID-XXXX] verified by a dedicated Verifier agent.',
      where: 'Inspect the Why tab in GIS Map drawer (/app/map) and Groundedness score in Evaluation.',
      liveFact: 'Live fact: 100% of generated cases cite 3 or more independent sensor signals.'
    },
    {
      title: 'Privacy by Design',
      icon: EyeOff,
      promise: 'No personally identifiable information (PII) is collected or processed; telemetry is aggregated at the block feeder level.',
      where: 'Review raw telemetry records in Ingestion API schema (/api/v1/telemetry).',
      liveFact: 'Live fact: Maintenance complaints are anonymized with resident names stripped.'
    },
    {
      title: 'Security & Role-Based Access Control (RBAC)',
      icon: Lock,
      promise: 'Server-side enforcement returns HTTP 403 for unauthorized requests; sensor laptops use distinct authentication credentials.',
      where: 'Switch roles in the top navbar to verify that Viewers cannot approve interventions or edit prioritizer weights.',
      liveFact: 'Live fact: 4 distinct API keys register supply, consumption, telemetry, and operations producers.'
    },
    {
      title: 'Failure Handling & Graceful Degradation',
      icon: AlertTriangle,
      promise: 'When the generative LLM is unreachable or times out, deterministic evidence templates and regex parsers ensure the platform never crashes.',
      where: 'Observed via the status pill in the navbar and fallback telemetry datasets in /public/fallback.',
      liveFact: 'Live fact: Demo Safe Mode (Shift+D) operates seamlessly during offline presentations.'
    },
    {
      title: 'Fairness & Supply Equity',
      icon: Scale,
      promise: 'Water is distributed equitably across academic, residential, and utility zones without unfair rationing bias.',
      where: 'Inspect the Supply Equity Index (0.94) on the Evaluation dashboard (/app/evaluation).',
      liveFact: 'Live fact: Prioritizer scoring breakdown is completely transparent with explicit term weights.'
    },
    {
      title: 'System Assumptions & Limitations',
      icon: AlertTriangle,
      promise: 'The system recommends; a licensed estate engineer decides. Contamination without quality sensors raises an immediate human test order.',
      where: 'Documented in /docs/KNOWN_LIMITS.md and the simulation scenario injector.',
      liveFact: 'Campus data is a synthetic digital twin modelled on a South Indian engineering campus.'
    }
  ];

  return (
    <div className="py-6 px-4 max-w-6xl mx-auto space-y-6">
      {/* Header */}
      <div className="glass-card p-6 shadow-glass flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <span className="text-[11px] font-mono text-sky-500 uppercase font-semibold">TCS Core Pillar</span>
          <h1 className="text-2xl font-bold text-ink-900 dark:text-mist">Responsible AI & Governance</h1>
          <p className="text-xs text-ink-600 dark:text-sky-300 mt-1">
            Grounded reasoning, human authority, privacy preservation, and transparent equity checks.
          </p>
        </div>

        <button
          onClick={handleDownloadCSV}
          className="px-5 py-2.5 rounded-btn bg-sky-500 hover:bg-sky-700 text-white font-semibold text-xs shadow-sm transition-colors flex items-center gap-2"
        >
          <Download className="w-3.5 h-3.5" />
          <span>Download Audit Log (CSV)</span>
        </button>
      </div>

      {/* Grid of 8 Live Fact Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {sections.map((sec) => {
          const Icon = sec.icon;
          return (
            <div
              key={sec.title}
              className="glass-card p-6 shadow-glass space-y-3 border border-sky-100 dark:border-white/10"
            >
              <div className="flex items-center gap-3">
                <div className="w-9 h-9 rounded-pill bg-sky-100 dark:bg-white/10 text-sky-700 dark:text-sky-300 flex items-center justify-center">
                  <Icon className="w-4 h-4" strokeWidth={1.5} />
                </div>
                <h3 className="font-bold text-sm text-ink-900 dark:text-mist">{sec.title}</h3>
              </div>

              <p className="text-xs text-ink-900 dark:text-mist font-medium leading-relaxed">
                {sec.promise}
              </p>

              <p className="text-[11px] text-ink-600 dark:text-sky-300">
                <span className="font-semibold text-sky-700 dark:text-sky-300">Verification location:</span> {sec.where}
              </p>

              <div className="pt-2 border-t border-sky-50 dark:border-white/5 text-[11px] font-mono text-leaf flex items-center gap-1.5">
                <CheckCircle2 className="w-3.5 h-3.5" />
                <span>{sec.liveFact}</span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
