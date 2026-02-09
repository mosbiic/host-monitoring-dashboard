export interface SystemMetrics {
  timestamp: number;
  cpu_percent: number;
  memory_percent: number;
  memory_used_gb: number;
  memory_total_gb: number;
  disk_percent: number;
  disk_used_gb: number;
  disk_total_gb: number;
  boot_time: number;
}

export interface ProcessInfo {
  name: string;
  running: boolean;
  pid: number | null;
  port: number | null;
  cpu_percent: number | null;
  memory_percent: number | null;
  uptime_seconds: number | null;
}

export interface ProcessMetrics {
  timestamp: number;
  processes: ProcessInfo[];
}

export interface HistoryDataPoint {
  timestamp: number;
  system: SystemMetrics | null;
  processes: ProcessInfo[] | null;
}

export interface HistoryResponse {
  hours: number;
  count: number;
  data: HistoryDataPoint[];
}

export type TimeRange = 24 | 168;
