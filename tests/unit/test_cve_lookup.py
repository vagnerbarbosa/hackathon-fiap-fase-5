"""Tests for the optional NVD CVE lookup client."""

import pytest

from src.services.cve_lookup import CveLookupClient


class FakeHttpResponse:
    def __init__(self, status_code: int, json_data: object) -> None:
        self.status_code = status_code
        self._json = json_data

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise RuntimeError("HTTP error")

    def json(self) -> object:
        return self._json


class FakeHttpClient:
    def __init__(self, response: FakeHttpResponse | Exception) -> None:
        self._response = response
        self.calls: list[dict] = []

    async def get(self, *args, **kwargs) -> FakeHttpResponse:
        self.calls.append({"args": args, "kwargs": kwargs})
        if isinstance(self._response, Exception):
            raise self._response
        return self._response


def test_client_disabled_without_api_key() -> None:
    client = CveLookupClient(api_key="")
    assert client.is_enabled is False


def test_client_enabled_with_api_key() -> None:
    client = CveLookupClient(api_key="secret")
    assert client.is_enabled is True


@pytest.mark.asyncio
async def test_search_returns_empty_when_disabled() -> None:
    client = CveLookupClient(api_key="")
    assert await client.search("CWE-287", "authentication") == []


@pytest.mark.asyncio
async def test_search_returns_empty_without_cwe_or_keyword() -> None:
    client = CveLookupClient(api_key="secret")
    assert await client.search(None, None) == []


@pytest.mark.asyncio
async def test_search_parses_cve_ids() -> None:
    payload = {
        "vulnerabilities": [
            {"cve": {"id": "CVE-2024-0001"}},
            {"cve": {"id": "CVE-2024-0002"}},
        ]
    }
    client = CveLookupClient(
        api_key="secret",
        http_client=FakeHttpClient(FakeHttpResponse(200, payload)),
    )

    result = await client.search("CWE-287", "authentication")

    assert result == ["CVE-2024-0001", "CVE-2024-0002"]


@pytest.mark.asyncio
async def test_search_limits_max_results() -> None:
    payload = {
        "vulnerabilities": [
            {"cve": {"id": f"CVE-2024-{i:04d}"}} for i in range(1, 10)
        ]
    }
    client = CveLookupClient(
        api_key="secret",
        max_results=3,
        http_client=FakeHttpClient(FakeHttpResponse(200, payload)),
    )

    result = await client.search("CWE-287")

    assert len(result) == 3


@pytest.mark.asyncio
async def test_search_deduplicates_cve_ids() -> None:
    payload = {
        "vulnerabilities": [
            {"cve": {"id": "CVE-2024-0001"}},
            {"cve": {"id": "CVE-2024-0001"}},
            {"cve": {"id": "CVE-2024-0002"}},
        ]
    }
    client = CveLookupClient(
        api_key="secret",
        http_client=FakeHttpClient(FakeHttpResponse(200, payload)),
    )

    result = await client.search("CWE-287")

    assert result == ["CVE-2024-0001", "CVE-2024-0002"]


@pytest.mark.asyncio
async def test_search_returns_empty_on_http_error() -> None:
    client = CveLookupClient(
        api_key="secret",
        http_client=FakeHttpClient(RuntimeError("network failure")),
    )

    assert await client.search("CWE-287") == []


@pytest.mark.asyncio
async def test_search_returns_empty_on_non_2xx_response() -> None:
    client = CveLookupClient(
        api_key="secret",
        http_client=FakeHttpClient(FakeHttpResponse(500, {})),
    )

    assert await client.search("CWE-287") == []


def test_parse_cve_ids_returns_empty_for_non_dict_payload() -> None:
    client = CveLookupClient(api_key="secret")
    assert client._parse_cve_ids("not-a-dict") == []


def test_parse_cve_ids_returns_empty_when_vulnerabilities_missing() -> None:
    client = CveLookupClient(api_key="secret")
    assert client._parse_cve_ids({}) == []


def test_parse_cve_ids_skips_invalid_entries() -> None:
    client = CveLookupClient(api_key="secret")
    payload = {
        "vulnerabilities": [
            "not-a-dict",
            {"cve": "not-a-dict"},
            {"cve": {"id": 123}},
            {"cve": {"id": "not-cve-format"}},
            {"cve": {"id": "CVE-2024-0001"}},
        ]
    }
    assert client._parse_cve_ids(payload) == ["CVE-2024-0001"]
