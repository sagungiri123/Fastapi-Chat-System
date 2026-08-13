import pytest
from fastapi.testclient import TestClient
from app.main import app

def test_websocket():
    client = TestClient(app)
    # First login to get token
    response = client.post("/api/v1/auth/login", data={"username": "test", "password": "test"})
    token = response.json()["access_token"]
    with client.websocket_connect(f"/ws/room1?token={token}") as websocket:
        websocket.send_text('{"content": "Hello"}')
        data = websocket.receive_text()
        assert "Hello" in data