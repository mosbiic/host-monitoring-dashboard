<template>
  <div class="min-h-screen flex items-center justify-center p-4">
    <div class="w-full max-w-md bg-gray-800 rounded-lg shadow-lg p-8">
      <div class="text-center mb-6">
        <h1 class="text-3xl font-bold mb-2">🔐 Login</h1>
        <p v-if="isCloudflareMode" class="text-gray-400">Authenticating via Cloudflare Access...</p>
        <p v-else-if="isLoadingConfig" class="text-gray-400">Loading configuration...</p>
        <p v-else class="text-gray-400">Enter your dashboard token to continue</p>
      </div>
      
      <!-- Cloudflare Access 模式显示加载状态 -->
      <div v-if="isCloudflareMode" class="text-center">
        <div class="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
        <p class="mt-4 text-gray-400">Waiting for Cloudflare Access authentication...</p>
      </div>

      <!-- 加载配置中 -->
      <div v-else-if="isLoadingConfig" class="text-center">
        <div class="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
      </div>
      
      <!-- 本地 Token 模式显示登录表单 -->
      <form v-else @submit.prevent="handleLogin" class="space-y-4">
        <div>
          <label class="block text-sm font-medium text-gray-300 mb-2">Token</label>
          <input
            v-model="tokenInput"
            type="password"
            class="input"
            placeholder="Enter your access token"
            required
          />
        </div>
        
        <div v-if="error" class="text-red-400 text-sm">
          {{ error }}
        </div>
        
        <button
          type="submit"
          class="btn btn-primary w-full"
          :disabled="loading"
        >
          <span v-if="loading">Logging in...</span>
          <span v-else>Login</span>
        </button>
      </form>
      
      <div class="mt-6 text-center text-xs text-gray-500">
        Host Monitoring Dashboard v1.0
        <span v-if="isCloudflareMode" class="block mt-1 text-blue-400">Cloudflare Access Enabled</span>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores'
import axios from 'axios'

export default {
  name: 'Login',
  setup() {
    const router = useRouter()
    const authStore = useAuthStore()
    
    const tokenInput = ref('')
    const loading = ref(false)
    const error = ref('')
    const isCloudflareMode = ref(false)
    const isLoadingConfig = ref(true)
    
    // 本地开发模式默认 Token
    const LOCAL_DEV_TOKEN = '43f4404377d1684d88fabbe5a2eb852af2d0f91955b9a6bd1d6aa26fed34ba9d'
    
    // 检测认证模式
    onMounted(async () => {
      try {
        // 1. 先查询后端配置，了解使用哪种认证模式
        const configResponse = await axios.get('/api/auth/config')
        const config = configResponse.data
        
        isLoadingConfig.value = false
        
        // 2. 如果启用了 Cloudflare Access
        if (config.cloudflare_access_enabled) {
          isCloudflareMode.value = true
          
          // 尝试访问受保护端点，如果成功说明已通过 CF Access 认证
          try {
            await axios.get('/api/metrics/system')
            authStore.enableCloudflareAccess()
            router.push('/dashboard')
          } catch (err) {
            // 如果返回 401，说明未通过 CF Access 认证
            // Cloudflare 会自动重定向到登录页，我们只需显示加载状态
            if (err.response?.status === 401) {
              console.log('Waiting for Cloudflare Access authentication...')
              // 页面会被 Cloudflare 重定向，不需要额外处理
            }
          }
          return
        }
        
        // 3. 本地 Token 模式：尝试使用默认 Token 自动登录（本地开发）
        if (!config.require_token || config.require_token === false) {
          try {
            await axios.get('/api/metrics/system')
            authStore.enableCloudflareAccess()
            router.push('/dashboard')
            return
          } catch (autoLoginErr) {
            // 自动登录失败，显示登录表单
            console.log('Auto-login failed, showing login form')
          }
        }
        
        // 4. 尝试使用本地存储的 Token 自动登录
        const savedToken = localStorage.getItem('dashboard_token')
        if (savedToken) {
          try {
            await axios.get('/api/metrics/system', {
              headers: {
                'Authorization': `Bearer ${savedToken}`
              }
            })
            authStore.setToken(savedToken)
            router.push('/dashboard')
            return
          } catch (tokenErr) {
            // Token 无效，清除并显示登录表单
            localStorage.removeItem('dashboard_token')
          }
        }
        
        // 5. 最后尝试使用默认开发 Token 自动登录
        if (!config.require_token) {
          try {
            await axios.get('/api/metrics/system', {
              headers: {
                'Authorization': `Bearer ${LOCAL_DEV_TOKEN}`
              }
            })
            authStore.setToken(LOCAL_DEV_TOKEN)
            router.push('/dashboard')
            return
          } catch (devTokenErr) {
            console.log('Dev token auto-login failed')
          }
        }
        
      } catch (err) {
        console.error('Failed to load auth config:', err)
        isLoadingConfig.value = false
        // 如果无法加载配置，回退到本地 Token 模式
        isCloudflareMode.value = false
      }
    })
    
    async function handleLogin() {
      loading.value = true
      error.value = ''
      
      try {
        // Set token temporarily for validation
        const testToken = tokenInput.value

        // Verify token by making a test request to an authenticated endpoint
        const response = await axios.get('/api/metrics/system', {
          headers: {
            'Authorization': `Bearer ${testToken}`
          }
        })
        
        // Token is valid, set it permanently and redirect
        authStore.setToken(testToken)
        router.push('/dashboard')
      } catch (err) {
        if (err.response?.status === 401) {
          error.value = 'Invalid token. Please check your token and try again.'
        } else if (err.response?.status === 403) {
          error.value = 'Access denied. Token may be expired or invalid.'
        } else if (err.code === 'ECONNREFUSED' || err.message?.includes('Network Error')) {
          error.value = 'Cannot connect to server. Please check if the backend is running.'
        } else {
          error.value = err.response?.data?.error || 'Invalid token or connection failed'
        }
      } finally {
        loading.value = false
      }
    }
    
    return {
      tokenInput,
      loading,
      error,
      isCloudflareMode,
      isLoadingConfig,
      handleLogin
    }
  }
}
</script>
