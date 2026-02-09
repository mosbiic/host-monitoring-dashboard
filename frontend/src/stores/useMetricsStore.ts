import { create } from 'zustand';
import type { SystemMetrics, ProcessMetrics, HistoryDataPoint, TimeRange } from '../types';

interface MetricsState {
  systemMetrics: SystemMetrics | null;
  processMetrics: ProcessMetrics | null;
  historyData: HistoryDataPoint[];
  wsConnected: boolean;
  wsError: string | null;
  timeRange: TimeRange;
  setSystemMetrics: (metrics: SystemMetrics) => void;
  setProcessMetrics: (metrics: ProcessMetrics) => void;
  setHistoryData: (data: HistoryDataPoint[]) => void;
  setWsConnected: (connected: boolean) => void;
  setWsError: (error: string | null) => void;
  setTimeRange: (range: TimeRange) => void;
  appendHistoryData: (data: HistoryDataPoint) => void;
}

export const useMetricsStore = create<MetricsState>((set, get) => ({
  systemMetrics: null,
  processMetrics: null,
  historyData: [],
  wsConnected: false,
  wsError: null,
  timeRange: 24,
  setSystemMetrics: (metrics) => set({ systemMetrics: metrics }),
  setProcessMetrics: (metrics) => set({ processMetrics: metrics }),
  setHistoryData: (data) => set({ historyData: data }),
  setWsConnected: (connected) => set({ wsConnected: connected }),
  setWsError: (error) => set({ wsError: error }),
  setTimeRange: (range) => set({ timeRange: range }),
  appendHistoryData: (data) => {
    const { historyData } = get();
    // Keep only last 500 points to prevent memory issues
    const newData = [...historyData, data].slice(-500);
    set({ historyData: newData });
  },
}));
