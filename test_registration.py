import asyncio
import httpx
import uuid

async def test():
    async with httpx.AsyncClient() as client:
        u1 = f"user_{uuid.uuid4().hex[:6]}"
        r1 = await client.post("http://127.0.0.1:8000/api/v1/auth/register", json={
            "username": u1,
            "email": f"{u1}@example.com",
            "password": "password123"
        })
        print(f"User 1 ({u1}):", r1.status_code, r1.text)

        u2 = f"user_{uuid.uuid4().hex[:6]}"
        r2 = await client.post("http://127.0.0.1:8000/api/v1/auth/register", json={
            "username": u2,
            "email": f"{u2}@example.com",
            "password": "password123"
        })
        print(f"User 2 ({u2}):", r2.status_code, r2.text)

asyncio.run(test())
