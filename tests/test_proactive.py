from starlette.testclient import TestClient
from main import app
from config.config import config

client = TestClient(app)

ROOM_ID = "23494025-aa7f-4765-9b1a-0aac89de379f"

response = client.post(
    f"/rooms/{ROOM_ID}/proactive",
    headers={"Authorization": f"Bearer {config.BACKEND_API_KEY}"},
)

print(response.content)