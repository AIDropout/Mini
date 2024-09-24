from starlette.testclient import TestClient
from main import app
from config.config import config

client = TestClient(app)

response = client.get(
    "/agents",
    headers={"Authorization": f"Bearer {config.BACKEND_API_KEY}"}
)

print(response.content)


