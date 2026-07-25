"""Tests for lazy exports in src.services."""

import pytest

import src.services as services


@pytest.mark.parametrize(
    "name",
    [
        "ComponentDetectionService",
        "NoComponentsDetectedError",
        "ImagePreprocessor",
        "RelationshipAnalyzer",
        "VulnerabilityService",
    ],
)
def test_services_lazy_exports(name: str) -> None:
    """Each exported name should be importable lazily."""
    obj = getattr(services, name)
    assert obj is not None


def test_services_unknown_attribute_raises_attribute_error() -> None:
    """Accessing an undefined attribute should raise AttributeError."""
    with pytest.raises(AttributeError):
        services.UnknownService  # noqa: B009,B018
