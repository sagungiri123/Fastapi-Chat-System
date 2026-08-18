import asyncio
import json
import httpx
import websockets

TEST_USERS = [
    ("alice_test", "testpass"),
    ("bob_test", "testpass"),
]

BASE_URL = "http://localhost:8000"
WS_BASE = "ws://localhost:8000"

async def ensure_user(client, username, password):
    # try register; ignore if fails
    try:
        resp = await client.post("/api/v1/auth/register", json={"username": username, "email": f"{username}@example.com", "password": password})
        if resp.status_code not in (200, 201):
            print(f"Register returned {resp.status_code}: {resp.text}")
    except Exception as e:
        print(f"Register request error: {e}")
    # login
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    data = {"username": username, "password": password}
    r = await client.post("/api/v1/auth/login", data=data, headers=headers)
    if r.status_code != 200:
        print(f"Login failed for {username}: {r.status_code} {r.text}")
        raise SystemExit(1)
    return r.json()["access_token"]

async def ws_listener(ws, queue, name):
    try:
        async for msg in ws:
            print(f"{name} recv: {msg}")
            try:
                queue.append(json.loads(msg))
            except Exception:
                queue.append(msg)
    except Exception as e:
        print(f"{name} listener error: {e}")

async def main():
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        t1 = await ensure_user(client, TEST_USERS[0][0], TEST_USERS[0][1])
        t2 = await ensure_user(client, TEST_USERS[1][0], TEST_USERS[1][1])

    uri1 = f"{WS_BASE}/ws/general?token={t1}"
    uri2 = f"{WS_BASE}/ws/general?token={t2}"

    recv1 = []
    recv2 = []

    async with websockets.connect(uri1) as ws1, websockets.connect(uri2) as ws2:
        task1 = asyncio.create_task(ws_listener(ws1, recv1, "alice"))
        task2 = asyncio.create_task(ws_listener(ws2, recv2, "bob"))

        await asyncio.sleep(0.5)

        # send message from alice
        await ws1.send(json.dumps({"type": "message", "content": "Hello from alice"}))

        await asyncio.sleep(1)

        # check that bob received it
        found = any((m.get("type") == "message" and "Hello from alice" in m.get("content", "")) for m in recv2 if isinstance(m, dict))

        if found:
            print("PASS: bob received alice message")
        else:
            print("FAIL: bob did not receive alice message")

        task1.cancel()
        task2.cancel()

if __name__ == "__main__":
    asyncio.run(main())
