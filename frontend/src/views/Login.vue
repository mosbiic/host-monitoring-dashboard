<template>
  <div class="min-h-screen flex items-center justify-center p-4">
    <div class="w-full max-w-md bg-gray-800 rounded-lg shadow-lg p-8">
      <div class="text-center mb-6">
        <h1 class="text-3xl font-bold mb-2">🔐 Login</h1>
        <p class="text-gray-400">Enter your dashboard token to continue</p>
      </div>
      
      <form @submit.prevent="handleLogin" class="space-y-4">
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
      </div>
    </div>
  </div>
</template>

<script>
import { ref } from 'vue'
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
      handleLogin
    }
  }
}
</script>
