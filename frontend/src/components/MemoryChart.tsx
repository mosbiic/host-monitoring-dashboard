import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler,
  type ChartOptions,
} from 'chart.js';
import { Line } from 'react-chartjs-2';
import type { HistoryDataPoint, TimeRange } from '../types';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
);

interface MemoryChartProps {
  data: HistoryDataPoint[];
  timeRange: TimeRange;
}

export function MemoryChart({ data, timeRange }: MemoryChartProps) {
  // Sort and downsample data
  const processedData = (() => {
    if (!data.length) return { labels: [], values: [] };

    const sortedData = [...data].sort((a, b) => a.timestamp - b.timestamp);
    
    // Downsample data for better performance
    const maxPoints = 200;
    let displayData = sortedData;
    if (sortedData.length > maxPoints) {
      const step = Math.ceil(sortedData.length / maxPoints);
      displayData = sortedData.filter((_, i) => i % step === 0);
    }

    const labels = displayData.map((d) => {
      const date = new Date(d.timestamp * 1000);
      if (timeRange <= 24) {
        return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
      }
      return date.toLocaleDateString([], { month: 'short', day: 'numeric', hour: '2-digit' });
    });

    const values = displayData.map((d) => d.system?.memory_percent || 0);

    return { labels, values };
  })();

  const chartData = {
    labels: processedData.labels,
    datasets: [
      {
        label: 'Memory %',
        data: processedData.values,
        borderColor: '#10b981',
        backgroundColor: 'rgba(16, 185, 129, 0.1)',
        borderWidth: 2,
        fill: true,
        tension: 0.3,
        pointRadius: 0,
        pointHitRadius: 10,
        pointHoverRadius: 4,
      },
    ],
  };

  const options: ChartOptions<'line'> = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        labels: { color: '#9ca3af' },
      },
      title: {
        display: false,
      },
    },
    scales: {
      x: {
        ticks: {
          color: '#9ca3af',
          maxTicksLimit: timeRange <= 24 ? 12 : 14,
          maxRotation: 45,
          minRotation: 45,
        },
        grid: { color: '#374151' },
      },
      y: {
        ticks: { color: '#9ca3af' },
        grid: { color: '#374151' },
        min: 0,
        max: 100,
      },
    },
    interaction: {
      intersect: false,
      mode: 'index',
    },
  };

  return (
    <div className="h-64">
      <Line data={chartData} options={options} />
    </div>
  );
}
