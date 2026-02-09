interface StatusIndicatorProps {
  connected: boolean;
}

export function StatusIndicator({ connected }: StatusIndicatorProps) {
  return (
    <div className="flex items-center gap-2">
      <div 
        className={`w-4 h-4 rounded-full ${
          connected ? 'bg-green-500' : 'bg-red-500'
        }`}
      />
      <span className="text-sm text-gray-400">
        {connected ? 'Connected' : 'Disconnected'}
      </span>
    </div>
  );
}
