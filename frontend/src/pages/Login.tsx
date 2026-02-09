import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { useAuthStore } from '../stores/useAuthStore';
import { Activity } from 'lucide-react';

export function Login() {
  const navigate = useNavigate();
  const { enableCloudflareAccess, isAuthenticated } = useAuthStore();

  useEffect(() => {
    // If already authenticated, redirect to dashboard
    if (isAuthenticated) {
      navigate('/dashboard', { replace: true });
      return;
    }

    const checkAuth = async () => {
      try {
        // Try to access protected endpoint to verify Cloudflare Access authentication
        console.log('[Login] Verifying Cloudflare Access authentication...');
        await axios.get('/api/metrics/system');
        console.log('[Login] CF Access auth verified, redirecting to dashboard');
        enableCloudflareAccess();
        navigate('/dashboard', { replace: true });
      } catch (err: any) {
        // If returns 401, CF Access authentication not completed
        if (err.response?.status === 401) {
          console.log('[Login] CF Access not authenticated (401)');
          // Cloudflare will automatically handle redirect
        } else {
          console.error('[Login] Error checking auth:', err.message);
        }
      }
    };

    checkAuth();
  }, [navigate, enableCloudflareAccess, isAuthenticated]);

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
