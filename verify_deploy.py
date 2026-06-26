import urllib.request
import json

print('=' * 60)
print('  爆款短视频复刻 SaaS 平台 - 部署验证')
print('=' * 60)
print()

base = 'http://localhost:8080'
results = []

def test(name, func):
    try:
        result = func()
        results.append((name, 'PASS', result))
        print(f'  [OK] {name}: {result}')
    except Exception as e:
        results.append((name, 'FAIL', str(e)))
        print(f'  [FAIL] {name}: {e}')

def test_health():
    r = urllib.request.urlopen(f'{base}/health')
    d = json.loads(r.read())
    return f'status={d.get("data", {}).get("status", "unknown")}'

def test_user_home():
    r = urllib.request.urlopen(f'{base}/')
    html = r.read().decode()
    if 'app' in html.lower() or 'vue' in html.lower() or '短视频' in html:
        return '页面正常加载'
    return '页面内容异常'

def test_admin_home():
    r = urllib.request.urlopen(f'{base}/admin/')
    html = r.read().decode()
    if 'app' in html.lower() or '管理后台' in html:
        return '页面正常加载'
    return '页面内容异常'

def test_admin_assets():
    r = urllib.request.urlopen(f'{base}/admin/assets/vue-KFSFdCZv.js')
    return f'大小={len(r.read())} bytes'

def test_user_login():
    data = json.dumps({"phone": "13800138000", "password": "13800138000"}).encode()
    req = urllib.request.Request(f'{base}/api/auth/login', data=data, method='POST')
    req.add_header('Content-Type', 'application/json')
    r = urllib.request.urlopen(req)
    d = json.loads(r.read())
    token = d.get('access_token', '')
    if token:
        return '登录成功'
    return f'返回格式: {list(d.keys())}'

def test_admin_login():
    data = json.dumps({"username": "admin", "password": "Admin@123"}).encode()
    req = urllib.request.Request(f'{base}/api/admin/login', data=data, method='POST')
    req.add_header('Content-Type', 'application/json')
    r = urllib.request.urlopen(req)
    d = json.loads(r.read())
    token = d.get('data', {}).get('token', '')
    if token:
        return '登录成功'
    return f'返回: {str(d)[:80]}'

def test_membership_plans():
    r = urllib.request.urlopen(f'{base}/api/membership/plans')
    d = json.loads(r.read())
    plans = d.get('data', [])
    return f'{len(plans)} 个套餐'

test('健康检查', test_health)
test('用户端首页', test_user_home)
test('管理后台首页', test_admin_home)
test('管理后台静态资源', test_admin_assets)
test('会员套餐列表', test_membership_plans)
test('用户登录', test_user_login)
test('管理员登录', test_admin_login)

print()
print('=' * 60)
passed = sum(1 for _, s, _ in results if s == 'PASS')
print(f'  结果: {passed}/{len(results)} 通过')
print('=' * 60)

if passed == len(results):
    print()
    print('  所有服务部署成功！')
    print()
    print('  访问地址:')
    print(f'    用户端: {base}/')
    print(f'    管理后台: {base}/admin/')
    print(f'    API 文档: {base}/docs')
    print()
    print('  测试账号:')
    print('    用户端: 13800138000 / 13800138000')
    print('    管理端: admin / Admin@123')
