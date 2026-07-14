"""Optional NVD CVE lookup client for Spec 005."""

import os
from typing import Any


class CveLookupClient:
    """Search CVE IDs from NVD when an API key is configured."""

    DEFAULT_BASE_URL = "https://services.nvd.nist.gov/rest/json/cves/2.0"

    def __init__(
        self,
        *,
        api_key: str | None = None,
        base_url: str = DEFAULT_BASE_URL,
        timeout_seconds: float = 5.0,
        max_results: int = 5,
        http_client: Any | None = None,
    ) -> None:
        self._api_key = api_key if api_key is not None else os.getenv("NVD_API_KEY")
        self._base_url = base_url
        self._timeout_seconds = timeout_seconds
        self._max_results = max_results
        self._http_client = http_client

    @property
    def is_enabled(self) -> bool:
        """Return True when NVD lookup should be attempted."""
        return bool(self._api_key)

    async def search(self, cwe_id: str | None, keyword: str | None = None) -> list[str]:
        """Return CVE IDs associated with a CWE or keyword."""
        if not self.is_enabled or (not cwe_id and not keyword):
            return []

        params: dict[str, str] = {"keywordSearch": keyword or cwe_id or ""}
        headers = {"apiKey": self._api_key or ""}

        try:
            if self._http_client is not None:
                response = await self._http_client.get(
                    self._base_url,
                    params=params,
                    headers=headers,
                    timeout=self._timeout_seconds,
                )
            else:
                import httpx

                async with httpx.AsyncClient(timeout=self._timeout_seconds) as client:
                    response = await client.get(
                        self._base_url,
                        params=params,
                        headers=headers,
                    )

            response.raise_for_status()
            return self._parse_cve_ids(response.json())
        except Exception:
            return []

    def _parse_cve_ids(self, payload: Any) -> list[str]:
        if not isinstance(payload, dict):
            return []

        vulnerabilities = payload.get("vulnerabilities")
        if not isinstance(vulnerabilities, list):
            return []

        cve_ids: list[str] = []
        seen: set[str] = set()
        for item in vulnerabilities:
            if not isinstance(item, dict):
                continue
            cve = item.get("cve")
            if not isinstance(cve, dict):
                continue
            cve_id = cve.get("id")
            if not isinstance(cve_id, str) or not cve_id.startswith("CVE-"):
                continue
            if cve_id in seen:
                continue
            seen.add(cve_id)
            cve_ids.append(cve_id)
            if len(cve_ids) >= self._max_results:
                break

        return cve_ids


__all__ = ["CveLookupClient"]
