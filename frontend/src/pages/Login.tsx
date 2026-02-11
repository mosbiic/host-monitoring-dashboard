import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { useAuthStore } from '../stores/useAuthStore';
import { Activity, Lock } from 'lucide-react';

export function Login() {
  const navigate = useNavigate();
  const { enableCloudflareAccess, isAuthenticated } = useAuthStore();
  const [token, setToken] = useState('');
  const [authMode, setAuthMode] = useState<'cloudflare' | 'token'>('cloudflare');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    // If already authenticated, redirect to dashboard
    if (isAuthenticated) {
      navigate('/dashboard', { replace: true });
      return;
    }

    const checkAuthConfig = async () => {
      try {
        // Check auth configuration
        const configRes = await axios.get('/api/auth/config');
        const { cloudflare_access_enabled, require_token } = configRes.data;
        
        console.log('[Login] Auth config:', configRes.data);
        
        if (!cloudflare_access_enabled && require_token) {
          setAuthMode('token');
          setLoading(false);
          return;
        }
        
        // Try Cloudflare Access authentication
        await checkCloudflareAuth();
      } catch (err: any) {
        console.error('[Login] Error checking auth config:', err.message);
        setLoading(false);
      }
    };

    const checkCloudflareAuth = async () => {
      try {
        console.log('[Login] Verifying Cloudflare Access authentication...');
        await axios.get('/api/metrics/system');
        console.log('[Login] CF Access auth verified, redirecting to dashboard');
        enableCloudflareAccess();
        navigate('/dashboard', { replace: true });
      } catch (err: any) {
        setLoading(false);
        if (err.response?.status === 401) {
          console.log('[Login] CF Access not authenticated (401)');
          // Cloudflare will automatically handle redirect
        } else {
          console.error('[Login] Error checking auth:', err.message);
        }
      }
    };

    checkAuthConfig();
  }, [navigate, enableCloudflareAccess, isAuthenticated]);

  const handleTokenSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    
    if (!token.trim()) {
      setError('Please enter a token');
      return;
    }

    try {
      // Test token by making an authenticated request
      await axios.get(`/api/metrics/system?token=${token}`);
      
      // Store token in axios defaults for subsequent requests
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
      
      // Mark as authenticated
      enableCloudflareAccess();
      navigate('/dashboard', { replace: true });
    } catch (err: any) {
      console.error('[Login] Token auth failed:', err.message);
      setError('Invalid token. Please try again.');
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center p-4">
        <div className="w-full max-w-md bg-gray-800 rounded-lg shadow-lg p-8 text-center">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
          <p className="mt-4 text-gray-400">Checking authentication...</p>
        </div>
      </div>
    );
  }

  if (authMode === 'token') {
    return (
      <div className="min-h-screen flex items-center justify-center p-4">
        <div className="w-full max-w-md bg-gray-800 rounded-lg shadow-lg p-8">
          <div className="text-center mb-6">
            <div className="flex justify-center mb-4">
              <Lock className="w-16 h-16 text-blue-500" />
            </div>
            <h1 className="text-3xl font-bold mb-2">🔐 访问监控面板</h1>
            <p className="text-gray-400">请输入访问令牌以继续</p>
          </div>

          <form onSubmit={handleTokenSubmit} className="space-y-4">
            <div>
              <label htmlFor="token" className="block text-sm font-medium text-gray-300 mb-2">
                Access Token
              </label>
              <input
                type="password"
                id="token"
                value={token}
                onChange={(e) => setToken(e.target.value)}
                className="w-full px-4 py-3 bg-gray-700 border border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-white"
                placeholder="Enter your access token"
                autoFocus
              />
            </div>

            {error && (
              <div className="p-3 bg-red-900/50 border border-red-700 rounded-lg text-red-300 text-sm">
                {error}
              </div>
            )}

            <button
              type="submit"
              className="w-full py-3 px-4 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-lg transition duration-200"
            >
              登录
            </button>
          </form>

          <div className="mt-6 text-center text-xs text-gray-500">
            Host Monitoring Dashboard v1.0
            <span className="block mt-1 text-yellow-400">Token Authentication Mode</span>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center p-4">
      <div className="w-full max-w-md bg-gray-800 rounded-lg shadow-lg p-8">
        <div className="text-center mb-6">
          <div className="flex justify-center mb-4">
            <Activity className="w-16 h-16 text-blue-500" />
          </div>
          <h1 className="text-3xl font-bold mb-2">🔐 认证中</h1>
          <p className="text-gray-400">正在通过 Cloudflare Access 认证...</p>
        </div>

        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
          <p className="mt-4 text-gray-400">请稍候，正在验证身份...</p>
        </div>

        <div className="mt-6 text-center text-xs text-gray-500">
          Host Monitoring Dashboard v1.0
          <span className="block mt-1 text-blue-400">Cloudflare Access Enabled</span>
        </div>
      </div>
    </div>
  );
}
