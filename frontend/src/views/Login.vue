<template>
  <div class="min-h-screen flex items-center justify-center p-4">
    <div class="w-full max-w-md bg-gray-800 rounded-lg shadow-lg p-8">
      <div class="text-center mb-6">
        <h1 class="text-3xl font-bold mb-2">🔐 认证中</h1>
        <p class="text-gray-400">正在通过 Cloudflare Access 认证...</p>
      </div>
      
      <div class="text-center">
        <div class="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
        <p class="mt-4 text-gray-400">请稍候，正在验证身份...</p>
      </div>
      
      <div class="mt-6 text-center text-xs text-gray-500">
        Host Monitoring Dashboard v1.0
        <span class="block mt-1 text-blue-400">Cloudflare Access Enabled</span>
      </div>
    </div>
  </div>
</template>

<script>
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores'
import axios from 'axios'

export default {
  name: 'Login',
  setup() {
    const router = useRouter()
    const authStore = useAuthStore()
    
    onMounted(async () => {
      try {
        // 尝试访问受保护端点验证 Cloudflare Access 认证
        console.log('[Login] Verifying Cloudflare Access authentication...')
        await axios.get('/api/metrics/system')
        console.log('[Login] CF Access auth verified, redirecting to dashboard')
        authStore.enableCloudflareAccess()
        router.replace('/dashboard')
      } catch (err) {
        // 如果返回 401，说明未通过 CF Access 认证
        if (err.response?.status === 401) {
          console.log('[Login] CF Access not authenticated (401)')
          // Cloudflare 会自动处理重定向
        } else {
          console.error('[Login] Error checking auth:', err.message)
        }
      }
    })
    
    return {}
  }
}
</script>
