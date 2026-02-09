#!/bin/bash
# 测试 Monitoring Dashboard 认证逻辑

echo "=== Testing Monitoring Dashboard Authentication ==="
echo ""

# 测试 1: 获取认证配置
echo "1. Testing /api/auth/config endpoint..."
curl -s http://localhost:8081/api/auth/config
echo ""
echo ""

# 测试 2: 无认证访问 (应该返回 401)
echo "2. Testing /api/metrics/system without auth (should return 401)..."
curl -s -w "\nHTTP Status: %{http_code}\n" http://localhost:8081/api/metrics/system
echo ""

# 测试 3: 使用本地 Token 访问
echo "3. Testing with local token..."
curl -s -w "\nHTTP Status: %{http_code}\n" -H "Authorization: Bearer 43f4404377d1684d88fabbe5a2eb852af2d0f91955b9a6bd1d6aa26fed34ba9d" http://localhost:8081/api/metrics/system | head -3
echo ""

# 测试 4: 使用 Cloudflare Access headers 访问
echo "4. Testing with Cloudflare Access headers..."
curl -s -w "\nHTTP Status: %{http_code}\n" -H "CF-Access-Authenticated-User-Email: test@example.com" http://localhost:8081/api/metrics/system | head -3
echo ""

# 测试 5: 测试本地开发模式自动登录 (需要临时修改 .env)
echo "5. To test auto-login mode (CF_ACCESS_ENABLED=false + DASHBOARD_TOKEN=changeme):"
echo "   - Set DASHBOARD_TOKEN=changeme in backend/.env"
echo "   - Restart backend"
echo "   - Access /api/metrics/system without token should succeed"
echo ""

echo "=== Test Complete ==="
