# Imports

from typing import Any, Dict, Optional
from decouple import config
import httpx

BASE_URL = config("BASE_URL", default="http://localhost:8000/")
USER_AGENT = config("USER_AGENT", default="transit-app/1.0")
HTTP_TIMEOUT = config("HTTP_TIMEOUT", default=10.0, cast=float)


class DatabusClient:
    """A client for interacting with the Databus API, providing methods to fetch data from various endpoints."""

    def __init__(
        self,
        base_url: str = BASE_URL,
        timeout: float = HTTP_TIMEOUT,
    ) -> None:
        self.base_url = base_url.rstrip("/") + "/"
        self._client = httpx.AsyncClient(
            timeout=timeout,
            headers={"User-Agent": USER_AGENT, "Accept": "application/json"},
        )

    async def _get_json(self, url: str) -> Any:
        """Helper method to perform a GET request and return the JSON response.

        arguments:
            - url: The URL to send the GET request to.

        returns:
            - The JSON response from the API if the request is successful.
            - Raises a RuntimeError if the request fails or the response is not valid JSON.
        """
        try:
            response = await self._client.get(url)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as exc:
            raise RuntimeError(f"HTTP error while requesting {url}: {exc}") from exc
        except ValueError as exc:
            raise RuntimeError(f"Invalid JSON response from {url}") from exc

    async def get_api(self, resource: str) -> Any:
        """Fetch data from a specific API resource.

        arguments:
            - resource: The API resource to fetch data from (e.g., "vehicles", "routes").

        returns:
            - The JSON response from the API for the specified resource.
            - Raises a RuntimeError if the request fails or the response is not valid JSON.
        """

        resource = resource.strip("/")
        url = f"{self.base_url}api/{resource}/?format=json"
        return await self._get_json(url)

    async def get_feed(self, path: str) -> Any:
        """Fetch real-time feed data from a specific path.

        arguments:
            - path: The path to the real-time feed data.

        returns:
            - The JSON response from the API for the specified feed path.
            - Raises a RuntimeError if the request fails or the response is not valid JSON.
        """

        path = path.strip("/")
        url = f"{self.base_url}feed/realtime/{path}.json"
        return await self._get_json(url)


_client: Optional[DatabusClient] = None


def get_client() -> DatabusClient:
    global _client
    if _client is None:
        _client = DatabusClient()
    return _client
