import { create } from 'zustand';

export type UserRole = 'admin' | 'student' | 'building_admin' | 'engineer';
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
  userId: string;
  setUserId: (id: string) => void;
  assignedBuildingId: string | null;
  setAssignedBuildingId: (id: string | null) => void;
  assignedEngineerId: string | null;
  setAssignedEngineerId: (id: string | null) => void;
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
    let uid = 'USER-ADMIN-01';
    let bld: string | null = null;
    let eng: string | null = null;
    if (role === 'student') {
      uid = 'USER-STUDENT-01';
      bld = 'BLK-HSTL-A';
    } else if (role === 'building_admin') {
      uid = 'USER-BLDADM-01';
      bld = 'BLK-HSTL-A';
    } else if (role === 'engineer') {
      uid = 'USER-ENG-01';
      eng = 'ENG-02';
      bld = 'BLK-HSTL-A';
    }
    sessionStorage.setItem('neeraran_user_id', uid);
    set({ role, userId: uid, assignedBuildingId: bld, assignedEngineerId: eng });
  },
  userId: sessionStorage.getItem('neeraran_user_id') || 'USER-ADMIN-01',
  setUserId: (userId) => {
    sessionStorage.setItem('neeraran_user_id', userId);
    set({ userId });
  },
  assignedBuildingId: 'BLK-HSTL-A',
  setAssignedBuildingId: (assignedBuildingId) => set({ assignedBuildingId }),
  assignedEngineerId: 'ENG-02',
  setAssignedEngineerId: (assignedEngineerId) => set({ assignedEngineerId }),
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
