"""Service module exports.

Exports are loaded lazily so importing a single service does not initialize
unrelated infrastructure such as API settings, ML models or cache clients.
"""

__all__ = [
    "ComponentDetectionService",
    "NoComponentsDetectedError",
    "ImagePreprocessor",
    "RelationshipAnalyzer",
    "VulnerabilityService",
]


def __getattr__(name: str) -> object:
    """Load service exports on demand."""
    if name in {"ComponentDetectionService", "NoComponentsDetectedError"}:
        from src.services.component_detector import (
            ComponentDetectionService,
            NoComponentsDetectedError,
        )

        return {
            "ComponentDetectionService": ComponentDetectionService,
            "NoComponentsDetectedError": NoComponentsDetectedError,
        }[name]

    if name == "ImagePreprocessor":
        from src.services.image_preprocessor import ImagePreprocessor

        return ImagePreprocessor

    if name == "RelationshipAnalyzer":
        from src.services.relationship_analyzer import RelationshipAnalyzer

        return RelationshipAnalyzer

    if name == "VulnerabilityService":
        from src.services.vulnerability_service import VulnerabilityService

        return VulnerabilityService

    raise AttributeError(f"module 'src.services' has no attribute {name!r}")
