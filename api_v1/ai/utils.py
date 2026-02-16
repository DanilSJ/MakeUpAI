from httpx import AsyncClient, ReadTimeout, HTTPStatusError
from core.config import settings


class AI:
    def __init__(self):
        self.token = settings.TOKEN_AI
        self.headers = {"Authorization": self.token}
        self.url_ai = settings.URL_AI
        self.timeout = 60.0

    async def send_request(self, model: str, prompt: str) -> str:
        async with AsyncClient(timeout=self.timeout) as client:
            try:
                result = await client.post(
                    url=self.url_ai,
                    headers=self.headers,
                    json={
                        "model": model,
                        "messages": [{"role": "user", "content": prompt}],
                    },
                )

                return result.json()["choices"][0]["message"]["content"]
            except ReadTimeout:
                raise ReadTimeout("Timeout reached")
            except HTTPStatusError as e:
                raise Exception(f"HTTP status error: {e.response.status_code}")
            except Exception as e:
                raise Exception(f"Unexpected error: {e}")

    async def deepseek(self, prompt: str) -> str:
        return await self.send_request("deepseek-v3.2", prompt)

    async def gemini(self, prompt: str) -> str:
        return await self.send_request("gemini-3-pro", prompt)

    async def claude(self, prompt: str) -> str:
        return await self.send_request("claude-4.6-opus", prompt)


ai = AI()
