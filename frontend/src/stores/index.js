import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import axios from 'axios'
import router from '../router'

const API_BASE = import.meta.env.VITE_API_BASE || ''

// Global axios interceptors for 401 handling
let onUnauthorizedCallback = null

export function setOnUnauthorizedCallback(callback) {
  onUnauthorizedCallback = callback
}

// Setup axios interceptors
axios.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      console.warn('Unauthorized: Token is invalid or expired')
      if (onUnauthorizedCallback) {
        onUnauthorizedCallback()
      }
    }
    return Promise.reject(error)
  }
)

export const useAuthStore = defineStore('auth', () => {
  const token = ref(localStorage.getItem('dashboard_token') || '')
  
  const isAuthenticated = computed(() => !!token.value)
  
  function setToken(newToken) {
    token.value = newToken
    localStorage.setItem('dashboard_token', newToken)
    axios.defaults.headers.common['Authorization'] = `Bearer ${newToken}`
  }
  
  function logout() {
    token.value = ''
    localStorage.removeItem('dashboard_token')
    delete axios.defaults.headers.common['Authorization']
  }
  
  // Initialize axios header if token exists
  if (token.value) {
    axios.defaults.headers.common['Authorization'] = `Bearer ${token.value}`
  }
  
  // Set up unauthorized callback
  setOnUnauthorizedCallback(() => {
    logout()
    router.push('/login')
  })
  
  return { token, isAuthenticated, setToken, logout }
})

export const useMetricsStore = defineStore('metrics', () => {
  const systemMetrics = ref(null)
  const processMetrics = ref(null)
  const historyData = ref([])
  const wsConnected = ref(false)
  const wsError = ref(null)
  
  let ws = null
  let reconnectTimeout = null
  
  async function fetchSystemMetrics() {
    try {
      const response = await axios.get(`${API_BASE}/api/metrics/system`)
      systemMetrics.value = response.data
      return response.data
    } catch (error) {
      console.error('Failed to fetch system metrics:', error)
      throw error
    }
  }
  
  async function fetchProcessMetrics() {
    try {
      const response = await axios.get(`${API_BASE}/api/metrics/processes`)
      processMetrics.value = response.data
      return response.data
    } catch (error) {
      console.error('Failed to fetch process metrics:', error)
      throw error
    }
  }
  
  async function fetchHistory(hours = 24) {
    try {
      const response = await axios.get(`${API_BASE}/api/metrics/history?hours=${hours}`)
      historyData.value = response.data.data
      return response.data
    } catch (error) {
      console.error('Failed to fetch history:', error)
      throw error
    }
  }
  
  function connectWebSocket(token, onAuthError = null) {
    if (ws) {
      ws.close()
    }
    
    // Use current window location for WebSocket connection
    // This ensures it works correctly through Cloudflare Tunnel
    const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const wsHost = window.location.host
    const wsUrl = `${wsProtocol}//${wsHost}/ws/metrics?token=${token}`
    
    console.log('Connecting WebSocket to:', wsUrl)
    
    ws = new WebSocket(wsUrl)
    
    ws.onopen = () => {
      console.log('WebSocket connected')
      wsConnected.value = true
      wsError.value = null
    }
    
    ws.onmessage = (event) => {
      try {
        // Handle ping/pong messages
        if (event.data === 'ping') {
          ws.send('pong')
          return
        }
        if (event.data === 'pong') {
          // Connection is alive
          return
        }
        
        const data = JSON.parse(event.data)
        
        // Check for auth errors from server
        if (data.error) {
          console.error('WebSocket error message:', data.error)
          if (data.error.includes('Unauthorized') || data.error.includes('Invalid token')) {
            wsConnected.value = false
            if (onAuthError) {
              onAuthError(true)
            }
            return
          }
        }
        
        if (data.system) {
          systemMetrics.value = data.system
        }
        if (data.processes) {
          processMetrics.value = { timestamp: data.timestamp, processes: data.processes }
        }
      } catch (error) {
        console.error('Failed to parse WebSocket message:', error, 'Data:', event.data)
      }
    }
    
    ws.onerror = (error) => {
      console.error('WebSocket error:', error)
      wsError.value = 'Connection error'
      wsConnected.value = false
    }
    
    ws.onclose = (event) => {
      console.log('WebSocket disconnected:', event.code, event.reason)
      wsConnected.value = false
      
      // Check if closed due to authentication (code 1008 = policy violation)
      if (event.code === 1008 || event.code === 1001) {
        console.warn('WebSocket closed possibly due to auth failure')
        if (onAuthError) {
          onAuthError(true)
          return
        }
      }
      
      // Auto-reconnect after 5 seconds (unless auth error)
      reconnectTimeout = setTimeout(() => {
        if (token && !wsConnected.value) {
          connectWebSocket(token, onAuthError)
        }
      }, 5000)
    }
  }
  
  function disconnectWebSocket() {
    if (reconnectTimeout) {
      clearTimeout(reconnectTimeout)
    }
    if (ws) {
      ws.close()
      ws = null
    }
    wsConnected.value = false
  }
  
  return {
    systemMetrics,
    processMetrics,
    historyData,
    wsConnected,
    wsError,
    fetchSystemMetrics,
    fetchProcessMetrics,
    fetchHistory,
    connectWebSocket,
    disconnectWebSocket
  }
})
