import { create } from 'zustand';

interface AuthState {
  isCloudflareAccess: boolean;
  isAuthenticated: boolean;
  enableCloudflareAccess: () => void;
  logout: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  isCloudflareAccess: false,
  isAuthenticated: false,
  enableCloudflareAccess: () => set({ 
    isCloudflareAccess: true, 
    isAuthenticated: true 
  }),
  logout: () => set({ 
    isCloudflareAccess: false, 
    isAuthenticated: false 
  }),
}));
