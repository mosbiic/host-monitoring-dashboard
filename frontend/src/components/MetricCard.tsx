import { Activity, Cpu, HardDrive, Clock, type LucideIcon } from 'lucide-react';

interface MetricCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  percent?: number | null;
  icon: 'cpu' | 'memory' | 'disk' | 'uptime';
  colorClass: string;
  barClass: string;
}

const iconMap: Record<string, LucideIcon> = {
  cpu: Cpu,
  memory: Activity,
  disk: HardDrive,
  uptime: Clock,
};

export function MetricCard({ 
  title, 
  value, 
  subtitle, 
  percent, 
  icon, 
  colorClass, 
  barClass 
}: MetricCardProps) {
  const Icon = iconMap[icon];

  return (
    <div className="bg-gray-800 rounded-lg p-6 card-hover transition">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          {Icon && <Icon className="w-6 h-6 text-gray-400" />}
          <span className="text-gray-300">{title}</span>
        </div>
        <span className={`text-3xl font-bold ${colorClass}`}>
          {value}
        </span>
      </div>
      
      {percent !== undefined && (
        <div className="h-2 bg-gray-700 rounded-full overflow-hidden">
          <div 
            className={`h-full transition-all duration-500 ${barClass}`}
            style={{ width: `${percent || 0}%` }}
          />
        </div>
      )}
      
      {subtitle && (
        <p className="text-sm text-gray-400 mt-2">{subtitle}</p>
      )}
    </div>
  );
}
