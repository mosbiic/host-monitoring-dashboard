import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useMetricsStore } from '../stores/useMetricsStore';
import { useAuthStore } from '../stores/useAuthStore';
import { useWebSocket } from '../hooks/useWebSocket';
import { useHistoryQuery } from '../hooks/useMetrics';
import { MetricCard } from '../components/MetricCard';
import { ProcessCard } from '../components/ProcessCard';
import { StatusIndicator } from '../components/StatusIndicator';
import { CpuChart } from '../components/CpuChart';
import { MemoryChart } from '../components/MemoryChart';
import {
  formatUptime,
  getCpuColorClass,
  getCpuBarClass,
  getMemoryColorClass,
  getMemoryBarClass,
  getDiskColorClass,
  getDiskBarClass,
} from '../utils/formatters';
import type { ProcessInfo, TimeRange } from '../types';

export function Dashboard() {
  const navigate = useNavigate();
  const { 
    systemMetrics, 
    processMetrics, 
    wsConnected, 
    timeRange, 
    setTimeRange, 
    setHistoryData 
  } = useMetricsStore();
  const { isAuthenticated } = useAuthStore();
  
  const { connect, disconnect } = useWebSocket(() => {
    navigate('/login');
  });

  // Fetch history data
  const { data: historyResponse } = useHistoryQuery(timeRange);

  // Update history data when query returns
  useEffect(() => {
    if (historyResponse?.data) {
      setHistoryData(historyResponse.data);
    }
  }, [historyResponse, setHistoryData]);

  // Connect WebSocket on mount
  useEffect(() => {
    if (isAuthenticated) {
      connect();
    }
    return () => {
      disconnect();
    };
  }, [isAuthenticated, connect, disconnect]);

  const handleTimeRangeChange = (range: TimeRange) => {
    setTimeRange(range);
  };

  // Categorize processes
  const openclawProcesses: ProcessInfo[] = (() => {
    const names = ['OpenClaw Gateway', 'OpenClaw Node', 'OpenClaw TUI'];
    return processMetrics?.processes?.filter((p) => names.includes(p.name)) || [];
  })();

  const externalProcesses: ProcessInfo[] = (() => {
    const names = ['Ollama', 'Cloudflared'];
    return processMetrics?.processes?.filter((p) => names.includes(p.name)) || [];
  })();

  const projectProcesses: ProcessInfo[] = (() => {
    const names = [
      'Monitoring Dashboard', 
      'Knowledge Graph API', 
      'Knowledge Graph UI', 
      'Personal Dashboard'
    ];
    return processMetrics?.processes?.filter((p) => names.includes(p.name)) || [];
  })();

  const historyData = historyResponse?.data || [];

  return (
    <div className="min-h-screen p-4">
      {/* Header */}
      <header className="flex justify-between items-center mb-6 p-4 bg-gray-800 rounded-lg">
        <div className="flex items-center gap-4">
          <StatusIndicator connected={wsConnected} />
          <div>
            <h1 className="text-2xl font-bold">📊 Host Monitoring Dashboard</h1>
            <p className="text-sm text-gray-400">Mac Mini System Status</p>
          </div>
        </div>

        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <button
              onClick={() => handleTimeRangeChange(24)}
              className={`px-4 py-2 rounded text-sm font-medium transition ${
                timeRange === 24
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
              }`}
            >
              24H
            </button>
            <button
              onClick={() => handleTimeRangeChange(168)}
              className={`px-4 py-2 rounded text-sm font-medium transition ${
                timeRange === 168
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
              }`}
            >
              7D
            </button>
          </div>
        </div>
      </header>

      {/* System Metrics Cards */}
      <section className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        <MetricCard
          title="CPU Usage"
          value={`${systemMetrics?.cpu_percent?.toFixed(1) || '--'}%`}
          percent={systemMetrics?.cpu_percent}
          icon="cpu"
          colorClass={getCpuColorClass(systemMetrics?.cpu_percent)}
          barClass={getCpuBarClass(systemMetrics?.cpu_percent)}
        />

        <MetricCard
          title="Memory"
          value={`${systemMetrics?.memory_percent?.toFixed(1) || '--'}%`}
          subtitle={`${systemMetrics?.memory_used_gb?.toFixed(2) || '--'} GB / ${systemMetrics?.memory_total_gb?.toFixed(2) || '--'} GB`}
          percent={systemMetrics?.memory_percent}
          icon="memory"
          colorClass={getMemoryColorClass(systemMetrics?.memory_percent)}
          barClass={getMemoryBarClass(systemMetrics?.memory_percent)}
        />

        <MetricCard
          title="Disk"
          value={`${systemMetrics?.disk_percent?.toFixed(1) || '--'}%`}
          subtitle={`${systemMetrics?.disk_used_gb?.toFixed(2) || '--'} GB / ${systemMetrics?.disk_total_gb?.toFixed(2) || '--'} GB`}
          percent={systemMetrics?.disk_percent}
          icon="disk"
          colorClass={getDiskColorClass(systemMetrics?.disk_percent)}
          barClass={getDiskBarClass(systemMetrics?.disk_percent)}
        />

        <MetricCard
          title="Uptime"
          value={formatUptime(systemMetrics?.boot_time)}
          icon="uptime"
          colorClass="text-blue-400"
          barClass=""
        />
      </section>

      {/* OpenClaw Core Services */}
      <section className="mb-6">
        <h2 className="text-xl font-bold mb-4">🔧 OpenClaw Core Services</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {openclawProcesses.map((proc) => (
            <ProcessCard key={proc.name} process={proc} />
          ))}
        </div>
      </section>

      {/* External Services */}
      <section className="mb-6">
        <h2 className="text-xl font-bold mb-4">🌐 External Services</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {externalProcesses.map((proc) => (
            <ProcessCard key={proc.name} process={proc} />
          ))}
        </div>
      </section>

      {/* Project Services */}
      <section className="mb-6">
        <h2 className="text-xl font-bold mb-4">📁 Project Services</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {projectProcesses.map((proc) => (
            <ProcessCard key={proc.name} process={proc} />
          ))}
        </div>
      </section>

      {/* Charts Section */}
      <section className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
        <div className="bg-gray-800 rounded-lg p-6">
          <div className="flex justify-between items-center mb-4">
            <h3 className="text-lg font-bold">📈 CPU Usage History</h3>
            <span className="text-sm text-gray-400">{timeRange}h</span>
          </div>
          <CpuChart data={historyData} timeRange={timeRange} />
        </div>

        <div className="bg-gray-800 rounded-lg p-6">
          <div className="flex justify-between items-center mb-4">
            <h3 className="text-lg font-bold">📈 Memory Usage History</h3>
            <span className="text-sm text-gray-400">{timeRange}h</span>
          </div>
          <MemoryChart data={historyData} timeRange={timeRange} />
        </div>
      </section>

      {/* Footer */}
      <footer className="mt-8 text-center text-sm text-gray-500">
        <p>Last updated: {new Date(systemMetrics?.timestamp || 0).toLocaleString()}</p>
        <p className="mt-1">WebSocket: {wsConnected ? '🟢 Connected' : '🔴 Disconnected'}</p>
        <p className="mt-1 text-gray-600">Data retention: 7 days</p>
      </footer>
    </div>
  );
}
