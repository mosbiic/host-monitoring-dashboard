import { useQuery } from '@tanstack/react-query';
import axios from 'axios';
import type { SystemMetrics, ProcessMetrics, HistoryResponse, TimeRange } from '../types';

const API_BASE = import.meta.env.VITE_API_BASE || '';

// Setup axios interceptors for 401 handling
axios.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      console.warn('[API] Unauthorized: Cloudflare Access authentication required');
    }
    return Promise.reject(error);
  }
);

export function useMetrics() {
  const fetchSystemMetrics = async (): Promise<SystemMetrics> => {
    const response = await axios.get(`${API_BASE}/api/metrics/system`);
    return response.data;
  };

  const fetchProcessMetrics = async (): Promise<ProcessMetrics> => {
    const response = await axios.get(`${API_BASE}/api/metrics/processes`);
    return response.data;
  };

  const fetchHistory = async (hours: TimeRange): Promise<HistoryResponse> => {
    const response = await axios.get(`${API_BASE}/api/metrics/history?hours=${hours}`);
    return response.data;
  };

  return {
    fetchSystemMetrics,
    fetchProcessMetrics,
    fetchHistory,
  };
}

export function useSystemMetricsQuery() {
  const { fetchSystemMetrics } = useMetrics();
  return useQuery({
    queryKey: ['systemMetrics'],
    queryFn: fetchSystemMetrics,
    refetchInterval: 30000, // Refetch every 30 seconds as backup
  });
}

export function useProcessMetricsQuery() {
  const { fetchProcessMetrics } = useMetrics();
  return useQuery({
    queryKey: ['processMetrics'],
    queryFn: fetchProcessMetrics,
    refetchInterval: 30000,
  });
}

export function useHistoryQuery(hours: TimeRange) {
  const { fetchHistory } = useMetrics();
  return useQuery({
    queryKey: ['history', hours],
    queryFn: () => fetchHistory(hours),
  });
}
