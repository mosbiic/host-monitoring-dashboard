# Monitoring Dashboard Redirect Loop Fix

## Problem Summary
The Monitoring Dashboard was experiencing an infinite redirect loop when using Cloudflare Access authentication:
1. Page displayed "Authenticating via Cloudflare Access..."
2. Then immediately redirected back to Login page
3. This cycle repeated indefinitely

## Root Cause Analysis

### Issue 1: Router Guard Incompatibility
- `router.js` only checked `localStorage.getItem('dashboard_token')` for authentication
- In Cloudflare Access mode, no token is stored in localStorage (auth is handled via CF headers)
- The router would redirect authenticated CF users back to login because it saw no token

### Issue 2: Login.vue Auto-Redirect
- `Login.vue` onMounted hook tried to auto-redirect on successful CF Access auth
- Used `router.push()` which added to history stack
- No protection against duplicate auth checks

### Issue 3: Race Condition
- Multiple redirect paths could trigger simultaneously
- No rate limiting on auth checks

## Solution Implemented

### 1. Updated `router.js`
```javascript
// Added auth store import
import { useAuthStore } from './stores'

// Added rate limiting
let authCheckTimestamp = 0
router.beforeEach((to, from, next) => {
  const now = Date.now()
  if (now - authCheckTimestamp < 2000 && to.path === from.path) {
    return next() // Prevent rapid auth checks
  }
  
  // Check Cloudflare Access mode
  const authStore = useAuthStore()
  const isCloudflareMode = authStore?.isCloudflareAccess || false
  
  if (isCloudflareMode) {
    // In CF mode, skip token checks - backend verifies CF headers
    if (to.path === '/login') {
      return next('/dashboard') // Already authenticated
    }
    return next()
  }
  
  // Standard token-based auth for non-CF mode
  // ...
})
```

### 2. Updated `Login.vue`
```javascript
// Added flag to prevent duplicate checks
let cfAuthChecked = false

onMounted(async () => {
  // ...
  if (config.cloudflare_access_enabled) {
    // Prevent duplicate CF auth checks
    if (cfAuthChecked) return
    cfAuthChecked = true
    
    try {
      await axios.get('/api/metrics/system')
      authStore.enableCloudflareAccess()
      router.replace('/dashboard') // Use replace, not push
    } catch (err) {
      if (err.response?.status === 401) {
        // Show CF waiting state - CF will handle redirect
      }
    }
  }
})
```

### 3. Added Debug Logging
- All auth flow events now log with `[Login]` or `[Router]` prefixes
- Makes it easy to trace issues in browser console

## Testing

### Local Mode (CF_ACCESS_ENABLED=false)
- ✅ Token-based authentication works
- ✅ Invalid tokens rejected (401)
- ✅ Valid tokens accepted (200)
- ✅ Auto-login with saved token works

### Cloudflare Access Mode (CF_ACCESS_ENABLED=true)
- ✅ No redirect loop
- ✅ Shows "Authenticating via Cloudflare Access..." while waiting
- ✅ Backend validates CF headers
- ✅ Router respects CF Access mode flag

## Files Changed
- `frontend/src/router.js` - Added CF Access awareness and rate limiting
- `frontend/src/views/Login.vue` - Added duplicate check prevention and better logging

## Deployment Notes
1. Build frontend: `cd frontend && npm run build`
2. Restart backend to pick up new static files
3. Monitor browser console for `[Login]` and `[Router]` debug logs

## Commit
```
commit 4716efa
Author: Mosbii
Date:   Sun Feb 8 19:32:00 2025

    fix: resolve Cloudflare Access login redirect loop
    
    - Added cfAuthChecked flag to prevent duplicate CF auth checks
    - Changed router.push() to router.replace() to avoid history issues
    - Router now checks isCloudflareAccess flag from auth store
    - Added rate limiting (2 second window) to prevent rapid auth checks
    - Added comprehensive debug logging for troubleshooting
```
