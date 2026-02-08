<template>
  <div class="min-h-screen p-4">
    <!-- Header -->
    <header class="flex justify-between items-center mb-6 p-4 bg-gray-800 rounded-lg">
      <div class="flex items-center gap-4">
        <div class="w-4 h-4 rounded-full" :class="wsConnected ? 'bg-green-500' : 'bg-red-500'"></div>
        <div>
          <h1 class="text-2xl font-bold">📊 Host Monitoring Dashboard</h1>
          <p class="text-sm text-gray-400">Mac Mini System Status</p>
        </div>
      </div>
      
      <div class="flex items-center gap-4">
        <div class="flex items-center gap-2">
          <button 
            @click="timeRange = 24" 
            :class="['btn btn-sm', timeRange === 24 ? 'btn-primary' : 'btn-secondary']"
          >
            24H
          </button>
          <button 
            @click="timeRange = 168" 
            :class="['btn btn-sm', timeRange === 168 ? 'btn-primary' : 'btn-secondary']"
          >
            7D
          </button>
        </div>
        <button @click="logout" class="btn btn-secondary">
          Logout
        </button>
      </div>
    </header>
    
    <!-- System Metrics Cards -->
    <section class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
      <!-- CPU Card -->
      <div class="bg-gray-800 rounded-lg p-6 card-hover transition">
        <div class="flex items-center justify-between mb-4">
          <div class="flex items-center gap-2">
            <span class="text-2xl">🖥️</span>
            <span class="text-gray-300">CPU Usage</span>
          </div>
          <span 
            class="text-3xl font-bold"
            :class="getCpuColorClass(systemMetrics?.cpu_percent)"
          >
            {{ systemMetrics?.cpu_percent?.toFixed(1) || '--' }}%
          </span>
        </div>
        <div class="h-2 bg-gray-700 rounded-full overflow-hidden">
          <div 
            class="h-full transition-all duration-500"
            :class="getCpuBarClass(systemMetrics?.cpu_percent)"
            :style="{ width: `${systemMetrics?.cpu_percent || 0}%` }"
          ></div>
        </div>
      </div>
      
      <!-- Memory Card -->
      <div class="bg-gray-800 rounded-lg p-6 card-hover transition">
        <div class="flex items-center justify-between mb-4">
          <div class="flex items-center gap-2">
            <span class="text-2xl">💾</span>
            <span class="text-gray-300">Memory</span>
          </div>
          <span 
            class="text-3xl font-bold"
            :class="getMemoryColorClass(systemMetrics?.memory_percent)"
          >
            {{ systemMetrics?.memory_percent?.toFixed(1) || '--' }}%
          </span>
        </div>
        <div class="h-2 bg-gray-700 rounded-full overflow-hidden mb-2">
          <div 
            class="h-full transition-all duration-500"
            :class="getMemoryBarClass(systemMetrics?.memory_percent)"
            :style="{ width: `${systemMetrics?.memory_percent || 0}%` }"
          ></div>
        </div>
        <p class="text-sm text-gray-400">
          {{ systemMetrics?.memory_used_gb?.toFixed(2) || '--' }} GB / {{ systemMetrics?.memory_total_gb?.toFixed(2) || '--' }} GB
        </p>
      </div>
      
      <!-- Disk Card -->
      <div class="bg-gray-800 rounded-lg p-6 card-hover transition">
        <div class="flex items-center justify-between mb-4">
          <div class="flex items-center gap-2">
            <span class="text-2xl">💿</span>
            <span class="text-gray-300">Disk</span>
          </div>
          <span 
            class="text-3xl font-bold"
            :class="getDiskColorClass(systemMetrics?.disk_percent)"
          >
            {{ systemMetrics?.disk_percent?.toFixed(1) || '--' }}%
          </span>
        </div>
        <div class="h-2 bg-gray-700 rounded-full overflow-hidden mb-2">
          <div 
            class="h-full transition-all duration-500"
            :class="getDiskBarClass(systemMetrics?.disk_percent)"
            :style="{ width: `${systemMetrics?.disk_percent || 0}%` }"
          ></div>
        </div>
        <p class="text-sm text-gray-400">
          {{ systemMetrics?.disk_used_gb?.toFixed(2) || '--' }} GB / {{ systemMetrics?.disk_total_gb?.toFixed(2) || '--' }} GB
        </p>
      </div>
      
      <!-- Uptime Card -->
      <div class="bg-gray-800 rounded-lg p-6 card-hover transition">
        <div class="flex items-center gap-2 mb-4">
          <span class="text-2xl">⏱️</span>
          <span class="text-gray-300">Uptime</span>
        </div>
        <div class="text-3xl font-bold text-blue-400">
          {{ formatUptime(systemMetrics?.boot_time) }}
        </div>
      </div>
    </section>
    
    <!-- OpenClaw Core Services -->
    <section class="mb-6">
      <h2 class="text-xl font-bold mb-4">🔧 OpenClaw Core Services</h2>
      
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <div 
          v-for="proc in openclawProcesses" 
          :key="proc.name"
          class="bg-gray-800 rounded-lg p-6 card-hover transition"
          :class="{ 'opacity-75': !proc.running }"
        >
          <div class="flex items-center justify-between mb-4">
            <div class="flex items-center gap-2">
              <div 
                class="w-3 h-3 rounded-full"
                :class="proc.running ? 'bg-green-500 animate-pulse' : 'bg-red-500'"
              ></div>
              <span class="font-bold">{{ proc.name }}</span>
            </div>
            <span 
              :class="proc.running ? 'text-green-400' : 'text-red-400'"
              class="text-sm font-medium"
            >
              {{ proc.running ? 'RUNNING' : 'STOPPED' }}
            </span>
          </div>
          
          <div class="space-y-2 text-sm">
            <div v-if="proc.pid" class="flex justify-between">
              <span class="text-gray-400">PID:</span>
              <span class="font-mono">{{ proc.pid }}</span>
            </div>
            
            <div v-if="proc.port" class="flex justify-between">
              <span class="text-gray-400">Port:</span>
              <span class="font-mono">{{ proc.port }}</span>
            </div>
            
            <div v-if="proc.cpu_percent !== null" class="flex justify-between">
              <span class="text-gray-400">CPU:</span>
              <span>{{ proc.cpu_percent }}%</span>
            </div>
            
            <div v-if="proc.memory_percent !== null" class="flex justify-between">
              <span class="text-gray-400">Memory:</span>
              <span>{{ proc.memory_percent.toFixed(2) }}%</span>
            </div>
            
            <div v-if="proc.uptime_seconds" class="flex justify-between">
              <span class="text-gray-400">Uptime:</span>
              <span>{{ formatDuration(proc.uptime_seconds) }}</span>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- External Services -->
    <section class="mb-6">
      <h2 class="text-xl font-bold mb-4">🌐 External Services</h2>
      
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <div 
          v-for="proc in externalProcesses" 
          :key="proc.name"
          class="bg-gray-800 rounded-lg p-6 card-hover transition"
          :class="{ 'opacity-75': !proc.running }"
        >
          <div class="flex items-center justify-between mb-4">
            <div class="flex items-center gap-2">
              <div 
                class="w-3 h-3 rounded-full"
                :class="proc.running ? 'bg-green-500 animate-pulse' : 'bg-red-500'"
              ></div>
              <span class="font-bold">{{ proc.name }}</span>
            </div>
            <span 
              :class="proc.running ? 'text-green-400' : 'text-red-400'"
              class="text-sm font-medium"
            >
              {{ proc.running ? 'RUNNING' : 'STOPPED' }}
            </span>
          </div>
          
          <div class="space-y-2 text-sm">
            <div v-if="proc.pid" class="flex justify-between">
              <span class="text-gray-400">PID:</span>
              <span class="font-mono">{{ proc.pid }}</span>
            </div>
            
            <div v-if="proc.port" class="flex justify-between">
              <span class="text-gray-400">Port:</span>
              <span class="font-mono">{{ proc.port }}</span>
            </div>
            
            <div v-if="proc.cpu_percent !== null" class="flex justify-between">
              <span class="text-gray-400">CPU:</span>
              <span>{{ proc.cpu_percent }}%</span>
            </div>
            
            <div v-if="proc.memory_percent !== null" class="flex justify-between">
              <span class="text-gray-400">Memory:</span>
              <span>{{ proc.memory_percent.toFixed(2) }}%</span>
            </div>
            
            <div v-if="proc.uptime_seconds" class="flex justify-between">
              <span class="text-gray-400">Uptime:</span>
              <span>{{ formatDuration(proc.uptime_seconds) }}</span>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- Project Services -->
    <section class="mb-6">
      <h2 class="text-xl font-bold mb-4">📁 Project Services</h2>
      
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <div 
          v-for="proc in projectProcesses" 
          :key="proc.name"
          class="bg-gray-800 rounded-lg p-6 card-hover transition"
          :class="{ 'opacity-75': !proc.running }"
        >
          <div class="flex items-center justify-between mb-4">
            <div class="flex items-center gap-2">
              <div 
                class="w-3 h-3 rounded-full"
                :class="proc.running ? 'bg-green-500 animate-pulse' : 'bg-red-500'"
              ></div>
              <span class="font-bold">{{ proc.name }}</span>
            </div>
            <span 
              :class="proc.running ? 'text-green-400' : 'text-red-400'"
              class="text-sm font-medium"
            >
              {{ proc.running ? 'RUNNING' : 'STOPPED' }}
            </span>
          </div>
          
          <div class="space-y-2 text-sm">
            <div v-if="proc.pid" class="flex justify-between">
              <span class="text-gray-400">PID:</span>
              <span class="font-mono">{{ proc.pid }}</span>
            </div>
            
            <div v-if="proc.port" class="flex justify-between">
              <span class="text-gray-400">Port:</span>
              <span class="font-mono">{{ proc.port }}</span>
            </div>
            
            <div v-if="proc.cpu_percent !== null" class="flex justify-between">
              <span class="text-gray-400">CPU:</span>
              <span>{{ proc.cpu_percent }}%</span>
            </div>
            
            <div v-if="proc.memory_percent !== null" class="flex justify-between">
              <span class="text-gray-400">Memory:</span>
              <span>{{ proc.memory_percent.toFixed(2) }}%</span>
            </div>
            
            <div v-if="proc.uptime_seconds" class="flex justify-between">
              <span class="text-gray-400">Uptime:</span>
              <span>{{ formatDuration(proc.uptime_seconds) }}</span>
            </div>
          </div>
        </div>
      </div>
    </section>
    
    <!-- Charts Section -->
    <section class="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
      <!-- CPU History Chart -->
      <div class="bg-gray-800 rounded-lg p-6">
        <div class="flex justify-between items-center mb-4">
          <h3 class="text-lg font-bold">📈 CPU Usage History</h3>
          <span class="text-sm text-gray-400">{{ timeRange }}h</span>
        </div>
        <div class="h-64">
          <canvas ref="cpuChart"></canvas>
        </div>
      </div>
      
      <!-- Memory History Chart -->
      <div class="bg-gray-800 rounded-lg p-6">
        <div class="flex justify-between items-center mb-4">
          <h3 class="text-lg font-bold">📈 Memory Usage History</h3>
          <span class="text-sm text-gray-400">{{ timeRange }}h</span>
        </div>
        <div class="h-64">
          <canvas ref="memoryChart"></canvas>
        </div>
      </div>
    </section>
    
    <!-- Footer -->
    <footer class="mt-8 text-center text-sm text-gray-500">
      <p>Last updated: {{ formatTime(systemMetrics?.timestamp) }}</p>
      <p class="mt-1">WebSocket: {{ wsConnected ? '🟢 Connected' : '🔴 Disconnected' }}</p>
      <p class="mt-1 text-gray-600">Data retention: 7 days</p>
    </footer>
  </div>
</template>

<script>
import { ref, computed, onMounted, onUnmounted, watch, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore, useMetricsStore } from '../stores'
import { Chart, registerables } from 'chart.js'

Chart.register(...registerables)

export default {
  name: 'Dashboard',
  setup() {
    const router = useRouter()
    const authStore = useAuthStore()
    const metricsStore = useMetricsStore()
    
    const timeRange = ref(24)
    const cpuChart = ref(null)
    const memoryChart = ref(null)
    let cpuChartInstance = null
    let memoryChartInstance = null
    
    const systemMetrics = computed(() => metricsStore.systemMetrics)
    const processMetrics = computed(() => metricsStore.processMetrics)
    const wsConnected = computed(() => metricsStore.wsConnected)
    const historyData = computed(() => metricsStore.historyData)
    
    // Categorize processes
    const openclawProcesses = computed(() => {
      const names = ['OpenClaw Gateway', 'OpenClaw Node', 'OpenClaw TUI']
      return processMetrics.value?.processes?.filter(p => names.includes(p.name)) || []
    })
    
    const externalProcesses = computed(() => {
      const names = ['Ollama', 'Cloudflared']
      return processMetrics.value?.processes?.filter(p => names.includes(p.name)) || []
    })
    
    const projectProcesses = computed(() => {
      const names = ['Monitoring Dashboard', 'Knowledge Graph API', 'Knowledge Graph UI', 'Personal Dashboard']
      return processMetrics.value?.processes?.filter(p => names.includes(p.name)) || []
    })
    
    function getCpuColorClass(percent) {
      if (!percent) return 'text-gray-400'
      if (percent < 50) return 'text-green-400'
      if (percent < 80) return 'text-yellow-400'
      return 'text-red-400'
    }
    
    function getCpuBarClass(percent) {
      if (!percent) return 'bg-gray-600'
      if (percent < 50) return 'bg-green-500'
      if (percent < 80) return 'bg-yellow-500'
      return 'bg-red-500'
    }
    
    function getMemoryColorClass(percent) {
      if (!percent) return 'text-gray-400'
      if (percent < 60) return 'text-green-400'
      if (percent < 85) return 'text-yellow-400'
      return 'text-red-400'
    }
    
    function getMemoryBarClass(percent) {
      if (!percent) return 'bg-gray-600'
      if (percent < 60) return 'bg-green-500'
      if (percent < 85) return 'bg-yellow-500'
      return 'bg-red-500'
    }
    
    function getDiskColorClass(percent) {
      if (!percent) return 'text-gray-400'
      if (percent < 70) return 'text-green-400'
      if (percent < 90) return 'text-yellow-400'
      return 'text-red-400'
    }
    
    function getDiskBarClass(percent) {
      if (!percent) return 'bg-gray-600'
      if (percent < 70) return 'bg-green-500'
      if (percent < 90) return 'bg-yellow-500'
      return 'bg-red-500'
    }
    
    function formatUptime(bootTime) {
      if (!bootTime) return '--'
      const now = Date.now() / 1000
      const uptime = now - bootTime
      return formatDuration(uptime)
    }
    
    function formatDuration(seconds) {
      if (!seconds) return '--'
      const days = Math.floor(seconds / 86400)
      const hours = Math.floor((seconds % 86400) / 3600)
      const mins = Math.floor((seconds % 3600) / 60)
      
      if (days > 0) return `${days}d ${hours}h ${mins}m`
      if (hours > 0) return `${hours}h ${mins}m`
      return `${mins}m`
    }
    
    function formatTime(timestamp) {
      if (!timestamp) return '--'
      return new Date(timestamp * 1000).toLocaleString()
    }
    
    function logout() {
      authStore.logout()
      metricsStore.disconnectWebSocket()
      router.push('/login')
    }
    
    function initCharts() {
      const commonOptions = {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            labels: { color: '#9ca3af' }
          }
        },
        scales: {
          x: {
            ticks: { 
              color: '#9ca3af', 
              maxTicksLimit: timeRange.value <= 24 ? 12 : 14,
              maxRotation: 45,
              minRotation: 45
            },
            grid: { color: '#374151' }
          },
          y: {
            ticks: { color: '#9ca3af' },
            grid: { color: '#374151' },
            min: 0,
            max: 100
          }
        },
        interaction: {
          intersect: false,
          mode: 'index'
        },
        elements: {
          point: {
            radius: 0,
            hitRadius: 10,
            hoverRadius: 4
          },
          line: {
            tension: 0.3
          }
        }
      }
      
      if (cpuChart.value) {
        cpuChartInstance = new Chart(cpuChart.value, {
          type: 'line',
          data: {
            labels: [],
            datasets: [{
              label: 'CPU %',
              data: [],
              borderColor: '#3b82f6',
              backgroundColor: 'rgba(59, 130, 246, 0.1)',
              borderWidth: 2,
              fill: true
            }]
          },
          options: commonOptions
        })
      }
      
      if (memoryChart.value) {
        memoryChartInstance = new Chart(memoryChart.value, {
          type: 'line',
          data: {
            labels: [],
            datasets: [{
              label: 'Memory %',
              data: [],
              borderColor: '#10b981',
              backgroundColor: 'rgba(16, 185, 129, 0.1)',
              borderWidth: 2,
              fill: true
            }]
          },
          options: commonOptions
        })
      }
    }
    
    function updateCharts() {
      if (!historyData.value.length) return
      
      // Sort by timestamp to ensure correct order
      const sortedData = [...historyData.value].sort((a, b) => a.timestamp - b.timestamp)
      
      // Downsample data for better performance with large datasets
      const maxPoints = 200
      let displayData = sortedData
      if (sortedData.length > maxPoints) {
        const step = Math.ceil(sortedData.length / maxPoints)
        displayData = sortedData.filter((_, i) => i % step === 0)
      }
      
      const labels = displayData.map(d => {
        const date = new Date(d.timestamp * 1000)
        if (timeRange.value <= 24) {
          return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
        }
        return date.toLocaleDateString([], { month: 'short', day: 'numeric', hour: '2-digit' })
      })
      
      const cpuData = displayData.map(d => d.system?.cpu_percent || 0)
      const memoryData = displayData.map(d => d.system?.memory_percent || 0)
      
      if (cpuChartInstance) {
        cpuChartInstance.data.labels = labels
        cpuChartInstance.data.datasets[0].data = cpuData
        cpuChartInstance.options.scales.x.ticks.maxTicksLimit = timeRange.value <= 24 ? 12 : 14
        cpuChartInstance.update('none')
      }
      
      if (memoryChartInstance) {
        memoryChartInstance.data.labels = labels
        memoryChartInstance.data.datasets[0].data = memoryData
        memoryChartInstance.options.scales.x.ticks.maxTicksLimit = timeRange.value <= 24 ? 12 : 14
        memoryChartInstance.update('none')
      }
    }
    
    watch(historyData, updateCharts, { deep: true })
    watch(timeRange, async (newRange) => {
      await metricsStore.fetchHistory(newRange)
      // Re-initialize charts to update x-axis tick settings
      if (cpuChartInstance) {
        cpuChartInstance.options.scales.x.ticks.maxTicksLimit = newRange <= 24 ? 12 : 14
        cpuChartInstance.update()
      }
      if (memoryChartInstance) {
        memoryChartInstance.options.scales.x.ticks.maxTicksLimit = newRange <= 24 ? 12 : 14
        memoryChartInstance.update()
      }
    })
    
    onMounted(async () => {
      // Check if token exists
      if (!authStore.token) {
        router.push('/login')
        return
      }
      
      // Initial data fetch with error handling
      try {
        await metricsStore.fetchSystemMetrics()
      } catch (error) {
        if (error.response?.status === 401) {
          // Token invalid, logout handled by interceptor
          return
        }
        console.error('Failed to fetch system metrics:', error)
      }
      
      try {
        await metricsStore.fetchProcessMetrics()
      } catch (error) {
        if (error.response?.status === 401) {
          return
        }
        console.error('Failed to fetch process metrics:', error)
      }
      
      try {
        await metricsStore.fetchHistory(timeRange.value)
      } catch (error) {
        if (error.response?.status === 401) {
          return
        }
        console.error('Failed to fetch history:', error)
      }
      
      // Connect WebSocket
      metricsStore.connectWebSocket(authStore.token, (isAuthError) => {
        if (isAuthError) {
          // WebSocket auth failed, logout and redirect
          logout()
        }
      })
      
      // Initialize charts
      await nextTick()
      initCharts()
      updateCharts()
    })
    
    onUnmounted(() => {
      metricsStore.disconnectWebSocket()
      if (cpuChartInstance) {
        cpuChartInstance.destroy()
      }
      if (memoryChartInstance) {
        memoryChartInstance.destroy()
      }
    })
    
    return {
      systemMetrics,
      processMetrics,
      openclawProcesses,
      externalProcesses,
      projectProcesses,
      wsConnected,
      timeRange,
      cpuChart,
      memoryChart,
      getCpuColorClass,
      getCpuBarClass,
      getMemoryColorClass,
      getMemoryBarClass,
      getDiskColorClass,
      getDiskBarClass,
      formatUptime,
      formatDuration,
      formatTime,
      logout
    }
  }
}
</script>
