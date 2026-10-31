import React from 'react';
import { useStore } from '../store/useStore';

export const StatusPill: React.FC = () => {
  const { demoSafeMode, sseConnected, simState } = useStore();

  if (demoSafeMode) {
    return (
      <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-pill text-xs font-medium bg-amber/15 text-amber border border-amber/30">
        <span className="w-2 h-2 rounded-full bg-amber animate-pulse"></span>
        <span>Demo safe mode</span>
      </div>
    );
  }

  if (sseConnected) {
    return (
      <div className="inline-flex items-center gap-2 px-3 py-1 rounded-pill text-xs font-medium bg-aqua/15 text-aqua border border-aqua/30">
        <span className="w-2 h-2 rounded-full bg-aqua animate-pulse"></span>
        <span>Live Twin • {simState?.speed_multiplier || 1}x</span>
      </div>
    );
  }

  return (
    <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-pill text-xs font-medium bg-coral/15 text-coral border border-coral/30">
      <span className="w-2 h-2 rounded-full bg-coral"></span>
      <span>Connecting</span>
    </div>
  );
};
