import { createRouter, createWebHistory } from 'vue-router'
import Dashboard from './views/Dashboard.vue'
import Login from './views/Login.vue'
import { useAuthStore } from './stores'

const routes = [
  { path: '/', redirect: '/dashboard' },
  { path: '/login', name: 'Login', component: Login },
  { path: '/dashboard', name: 'Dashboard', component: Dashboard, meta: { requiresAuth: true } }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// Track if we're currently checking auth to prevent redirect loops
let isCheckingAuth = false
let authCheckTimestamp = 0

router.beforeEach((to, from, next) => {
  // Prevent rapid repeated auth checks (within 2 seconds)
  const now = Date.now()
  if (isCheckingAuth || (now - authCheckTimestamp < 2000 && to.path === from.path)) {
    console.log('[Router] Auth check already in progress or too frequent, allowing navigation')
    return next()
  }
  
  authCheckTimestamp = now
  
  // Get auth store - this works because Pinia is initialized before router
  let authStore = null
  try {
    authStore = useAuthStore()
  } catch (e) {
    console.log('[Router] Auth store not available yet')
  }
  
  const token = localStorage.getItem('dashboard_token')
  const isCloudflareMode = authStore?.isCloudflareAccess || false
  
  console.log(`[Router] Navigating to ${to.path}, token=${!!token}, cfMode=${isCloudflareMode}`)
  
  // If Cloudflare Access mode is enabled, skip token-based auth checks
  // The backend will verify CF headers
  if (isCloudflareMode) {
    if (to.path === '/login') {
      // If authenticated via CF and trying to go to login, redirect to dashboard
      console.log('[Router] CF mode: already authenticated, redirecting to dashboard')
      return next('/dashboard')
    }
    return next()
  }
  
  // Standard token-based auth
  if (to.meta.requiresAuth && !token) {
    console.log('[Router] No token, redirecting to login')
    return next('/login')
  } else if (to.path === '/login' && token) {
    console.log('[Router] Has token, redirecting to dashboard')
    return next('/dashboard')
  } else {
    next()
  }
})

export default router
