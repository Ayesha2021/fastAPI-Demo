
import httpx
from pydantic import BaseModel
import asyncio


class FastAPIClient:
    def __init__(self, base_url: str, token: str | None = None):
        headers = {"Authorization": f"Bearer {token}"} if token else {}
        self.client = httpx.AsyncClient(
            base_url=base_url,
            headers=headers,
            timeout=10.0,
        )


async def main():
    api = FastAPIClient(base_url="http://localhost:8000",
                        token="your-jwt-token")
    try:
        todos = await api.client.get("/toddos")
        print(f"Created: {todos}")

    except httpx.HTTPStatusError as e:
        print(f"API error {e.response.status_code}: {e.response.text}")
    # finally:
        # await api.close()


asyncio.run(main())
