path = r'd:\ai\codex\爆款短视频复刻\frontend-user\src\views\Login.vue'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

old = "'验证码登录''\" name=\"sms\">"
new = "'验证码登录'\" name=\"sms\">"

if old in content:
    content = content.replace(old, new)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print('Replaced successfully')
else:
    print('Old string not found')
    for i, line in enumerate(content.split('\n'), 1):
        if '验证码登录' in line:
            print(f'Line {i}: {repr(line)}')
