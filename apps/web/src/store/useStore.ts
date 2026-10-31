import { create } from 'zustand';

export type UserRole = 'admin' | 'viewer';
export type ViewerLens = 'warden' | 'sustainability' | 'student' | 'maintenance';

export interface SimulationState {
  tick: number;
  timestamp: string;
  formatted_time: string;
  hour: number;
  is_weekend: boolean;
  speed_multiplier: number;
  total_consumption_lpm: number;
  total_inflow_lpm: number;
  total_stored_kl: number;
  days_of_reserve: number;
  weather: {
    temperature_c: number;
    rainfall_mm_hr: number;
    heatwave: boolean;
  };
  tanks: Record<string, { current_kl: number; capacity_kl: number; fill_pct: number; safety_level_kl: number }>;
  block_meters: Record<string, number>;
  pressures: Record<string, number>;
  borewells: Record<string, { yield_lpm: number; running: boolean }>;
  active_faults_ground_truth: any[];
  complaints: any[];
}

interface AppStore {
  role: UserRole;
  setRole: (role: UserRole) => void;
  viewerLens: ViewerLens;
  setViewerLens: (lens: ViewerLens) => void;
  isNightOps: boolean;
  toggleNightOps: () => void;
  demoSafeMode: boolean;
  toggleDemoSafeMode: () => void;
  simState: SimulationState | null;
  setSimState: (state: SimulationState) => void;
  selectedCaseId: string | null;
  setSelectedCaseId: (id: string | null) => void;
  selectedAssetId: string | null;
  setSelectedAssetId: (id: string | null) => void;
  sseConnected: boolean;
  setSseConnected: (status: boolean) => void;
}

export const useStore = create<AppStore>((set) => ({
  role: (sessionStorage.getItem('neeraran_role') as UserRole) || 'admin',
  setRole: (role) => {
    sessionStorage.setItem('neeraran_role', role);
    set({ role });
  },
  viewerLens: 'warden',
  setViewerLens: (viewerLens) => set({ viewerLens }),
  isNightOps: false,
  toggleNightOps: () => {
    set((state) => {
      const next = !state.isNightOps;
      if (next) {
        document.documentElement.classList.add('dark');
      } else {
        document.documentElement.classList.remove('dark');
      }
      return { isNightOps: next };
    });
  },
  demoSafeMode: false,
  toggleDemoSafeMode: () => set((state) => ({ demoSafeMode: !state.demoSafeMode })),
  simState: null,
  setSimState: (simState) => set({ simState }),
  selectedCaseId: null,
  setSelectedCaseId: (selectedCaseId) => set({ selectedCaseId }),
  selectedAssetId: null,
  setSelectedAssetId: (selectedAssetId) => set({ selectedAssetId }),
  sseConnected: false,
  setSseConnected: (sseConnected) => set({ sseConnected }),
}));
