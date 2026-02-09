export function formatDuration(seconds: number | null | undefined): string {
  if (!seconds) return '--';
  const days = Math.floor(seconds / 86400);
  const hours = Math.floor((seconds % 86400) / 3600);
  const mins = Math.floor((seconds % 3600) / 60);

  if (days > 0) return `${days}d ${hours}h ${mins}m`;
  if (hours > 0) return `${hours}h ${mins}m`;
  return `${mins}m`;
}

export function formatUptime(bootTime: number | null | undefined): string {
  if (!bootTime) return '--';
  const now = Date.now() / 1000;
  const uptime = now - bootTime;
  return formatDuration(uptime);
}

export function formatTime(timestamp: number | null | undefined): string {
  if (!timestamp) return '--';
  return new Date(timestamp * 1000).toLocaleString();
}

export function getCpuColorClass(percent: number | null | undefined): string {
  if (!percent) return 'text-gray-400';
  if (percent < 50) return 'text-green-400';
  if (percent < 80) return 'text-yellow-400';
  return 'text-red-400';
}

export function getCpuBarClass(percent: number | null | undefined): string {
  if (!percent) return 'bg-gray-600';
  if (percent < 50) return 'bg-green-500';
  if (percent < 80) return 'bg-yellow-500';
  return 'bg-red-500';
}

export function getMemoryColorClass(percent: number | null | undefined): string {
  if (!percent) return 'text-gray-400';
  if (percent < 60) return 'text-green-400';
  if (percent < 85) return 'text-yellow-400';
  return 'text-red-400';
}

export function getMemoryBarClass(percent: number | null | undefined): string {
  if (!percent) return 'bg-gray-600';
  if (percent < 60) return 'bg-green-500';
  if (percent < 85) return 'bg-yellow-500';
  return 'bg-red-500';
}

export function getDiskColorClass(percent: number | null | undefined): string {
  if (!percent) return 'text-gray-400';
  if (percent < 70) return 'text-green-400';
  if (percent < 90) return 'text-yellow-400';
  return 'text-red-400';
}

export function getDiskBarClass(percent: number | null | undefined): string {
  if (!percent) return 'bg-gray-600';
  if (percent < 70) return 'bg-green-500';
  if (percent < 90) return 'bg-yellow-500';
  return 'bg-red-500';
}
