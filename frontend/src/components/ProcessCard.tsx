import type { ProcessInfo } from '../types';
import { formatDuration } from '../utils/formatters';

interface ProcessCardProps {
  process: ProcessInfo;
}

export function ProcessCard({ process }: ProcessCardProps) {
  return (
    <div 
      className={`bg-gray-800 rounded-lg p-6 card-hover transition ${
        !process.running ? 'opacity-75' : ''
      }`}
    >
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <div 
            className={`w-3 h-3 rounded-full ${
              process.running ? 'bg-green-500 animate-pulse' : 'bg-red-500'
            }`}
          />
          <span className="font-bold">{process.name}</span>
        </div>
        <span 
          className={`text-sm font-medium ${
            process.running ? 'text-green-400' : 'text-red-400'
          }`}
        >
          {process.running ? 'RUNNING' : 'STOPPED'}
        </span>
      </div>

      <div className="space-y-2 text-sm">
        {process.pid !== null && (
          <div className="flex justify-between">
            <span className="text-gray-400">PID:</span>
            <span className="font-mono">{process.pid}</span>
          </div>
        )}

        {process.port !== null && (
          <div className="flex justify-between">
            <span className="text-gray-400">Port:</span>
            <span className="font-mono">{process.port}</span>
          </div>
        )}

        {process.cpu_percent !== null && (
          <div className="flex justify-between">
            <span className="text-gray-400">CPU:</span>
            <span>{process.cpu_percent}%</span>
          </div>
        )}

        {process.memory_percent !== null && (
          <div className="flex justify-between">
            <span className="text-gray-400">Memory:</span>
            <span>{process.memory_percent.toFixed(2)}%</span>
          </div>
        )}

        {process.uptime_seconds !== null && (
          <div className="flex justify-between">
            <span className="text-gray-400">Uptime:</span>
            <span>{formatDuration(process.uptime_seconds)}</span>
          </div>
        )}
      </div>
    </div>
  );
}
