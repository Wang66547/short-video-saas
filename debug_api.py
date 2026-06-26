import urllib.request
import json

print('=== 调试：健康检查 ===')
resp = urllib.request.urlopen('http://localhost:8080/health')
print(f'Status: {resp.status}')
raw = resp.read().decode()
print(f'Raw: {raw[:500]}')
print()

print('=== 调试：用户登录 ===')
data = json.dumps({"phone": "13800138000", "password": "13800138000"}).encode()
req = urllib.request.Request('http://localhost:8080/api/auth/login', data=data, method='POST')
req.add_header('Content-Type', 'application/json')
resp = urllib.request.urlopen(req)
print(f'Status: {resp.status}')
raw = resp.read().decode()
print(f'Raw: {raw[:500]}')
print()

print('=== 调试：管理员登录 ===')
data = json.dumps({"username": "admin", "password": "Admin@123"}).encode()
req = urllib.request.Request('http://localhost:8080/api/admin/login', data=data, method='POST')
req.add_header('Content-Type', 'application/json')
resp = urllib.request.urlopen(req)
print(f'Status: {resp.status}')
raw = resp.read().decode()
print(f'Raw: {raw[:500]}')
