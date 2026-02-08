<template>
  <div class="min-h-screen flex items-center justify-center p-4">
    <div class="w-full max-w-md bg-gray-800 rounded-lg shadow-lg p-8">
      <div class="text-center mb-6">
        <h1 class="text-3xl font-bold mb-2">🔐 Login</h1>
        <p v-if="!isCloudflareMode" class="text-gray-400">Enter your dashboard token to continue</p>
        <p v-else class="text-gray-400">Redirecting to Cloudflare Access...</p>
      </div>
      
      <!-- Cloudflare Access 模式显示加载状态 -->
      <div v-if="isCloudflareMode" class="text-center">
        <div class="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
        <p class="mt-4 text-gray-400">Authenticating via Cloudflare Access...</p>
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
    
    // 本地开发模式默认 Token
    const LOCAL_DEV_TOKEN = '43f4404377d1684d88fabbe5a2eb852af2d0f91955b9a6bd1d6aa26fed34ba9d'
    
    // 检测是否在 Cloudflare Access 环境下
    onMounted(async () => {
      // 尝试访问一个需要认证的端点，如果返回 401 则需要登录
      // 如果成功，说明已经通过 Cloudflare Access 认证
      try {
        const response = await axios.get('/api/metrics/system')
        // 如果成功，说明已经认证，直接跳转到 dashboard
        authStore.enableCloudflareAccess()
        router.push('/dashboard')
      } catch (err) {
        if (err.response?.status === 401) {
          // 检查是否是 Cloudflare Access 返回的 401
          // Cloudflare Access 会在用户未登录时自动重定向到登录页
          // 所以如果能访问 /login 页面但没有认证，说明是本地 Token 模式
          isCloudflareMode.value = false
          
          // 本地开发模式：尝试使用默认 Token 自动登录
          try {
            const testResponse = await axios.get('/api/metrics/system', {
              headers: {
                'Authorization': `Bearer ${LOCAL_DEV_TOKEN}`
              }
            })
            // 默认 Token 有效，自动登录
            authStore.setToken(LOCAL_DEV_TOKEN)
            router.push('/dashboard')
          } catch (autoLoginErr) {
            // 默认 Token 无效，保持登录页面显示
            console.log('Auto-login failed, showing login form')
          }
        }
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
      handleLogin
    }
  }
}
</script>
