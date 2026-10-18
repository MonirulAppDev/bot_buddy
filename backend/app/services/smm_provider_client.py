import httpx
import logging
from typing import Any

logger = logging.getLogger("smm_provider_client")


class SMMProviderClient:
    """Client for upstream SMM Panel API v2 providers to deliver real bot likes at scale."""

    def __init__(self, api_url: str, api_key: str):
        self.api_url = api_url.rstrip("/")
        self.api_key = api_key

    async def get_services(self) -> list[dict[str, Any]]:
        """Fetch available services from upstream SMM provider."""
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(self.api_url, data={"key": self.api_key, "action": "services"})
            resp.raise_for_status()
            return resp.json()

    async def get_balance(self) -> dict[str, Any]:
        """Fetch balance from upstream SMM provider."""
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(self.api_url, data={"key": self.api_key, "action": "balance"})
            resp.raise_for_status()
            return resp.json()

    async def place_order(
        self,
        service_id: int,
        link: str,
        quantity: int,
        comments: str | None = None
    ) -> dict[str, Any]:
        """Send order to upstream provider bot farm."""
        payload = {
            "key": self.api_key,
            "action": "add",
            "service": service_id,
            "link": link,
            "quantity": quantity
        }
        if comments:
            payload["comments"] = comments

        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(self.api_url, data=payload)
            resp.raise_for_status()
            return resp.json()

    async def get_order_status(self, order_id: str) -> dict[str, Any]:
        """Check order status on upstream provider."""
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(self.api_url, data={"key": self.api_key, "action": "status", "order": order_id})
            resp.raise_for_status()
            return resp.json()
