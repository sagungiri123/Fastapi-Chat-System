import asyncio
import websockets
import json
import httpx
import uuid

async def test():
    async with httpx.AsyncClient() as client:
        # Register a new user
        u = f"wsuser_{uuid.uuid4().hex[:6]}"
        await client.post("http://127.0.0.1:8000/api/v1/auth/register", json={
            "username": u,
            "email": f"{u}@example.com",
            "password": "password123"
        })
        # Login
        r = await client.post("http://127.0.0.1:8000/api/v1/auth/login", data={
            "username": u,
            "password": "password123"
        })
        token = r.json()["access_token"]
        
    print(f"Got token: {token}")
    
    uri = f"ws://127.0.0.1:8000/ws/testroom?token={token}"
    try:
        async with websockets.connect(uri) as ws:
            print("Connected to WS")
            await ws.send(json.dumps({"content": "hello"}))
            print("Sent message")
            
            # Wait for response
            try:
                resp = await asyncio.wait_for(ws.recv(), timeout=2.0)
                print("Received:", resp)
            except asyncio.TimeoutError:
                print("No response from server")
            
    except Exception as e:
        print("WS Error:", e)

asyncio.run(test())
