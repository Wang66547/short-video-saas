"""
API测试脚本
验证用户体系接口是否正常工作
"""
import asyncio
import httpx
from app.core.config import get_settings

settings = get_settings()


async def test_health():
    """测试健康检查接口"""
    async with httpx.AsyncClient() as client:
        response = await client.get("http://localhost:8000/health")
        print(f"Health check: {response.status_code} - {response.json()}")


async def test_send_code():
    """测试发送验证码"""
    async with httpx.AsyncClient() as client:
        response = await client.post("http://localhost:8000/api/auth/send-code", params={"phone": "13800138000"})
        print(f"Send code: {response.status_code} - {response.json()}")


async def test_register():
    """测试用户注册"""
    async with httpx.AsyncClient() as client:
        data = {
            "phone": "13800138000",
            "captcha": "1234",  # 测试验证码
            "password": "123456",
            "nickname": "测试用户"
        }
        response = await client.post("http://localhost:8000/api/auth/register", json=data)
        print(f"Register: {response.status_code} - {response.json()}")


async def test_login():
    """测试用户登录"""
    async with httpx.AsyncClient() as client:
        data = {
            "phone": "13800138000",
            "password": "123456"
        }
        response = await client.post("http://localhost:8000/api/auth/login", json=data)
        print(f"Login: {response.status_code} - {response.json()}")


async def main():
    """运行所有测试"""
    print("Starting API tests...")
    await test_health()
    await test_send_code()
    await test_register()
    await test_login()
    print("Tests completed!")


if __name__ == "__main__":
    asyncio.run(main())
