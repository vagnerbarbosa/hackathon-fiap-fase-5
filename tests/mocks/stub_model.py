"""
tests/mocks/stub_model.py
==========================
Stub do modelo YOLO para uso em testes das specs que dependem de inferência
(Spec 003 e seguintes) antes de best.pt estar disponível.

Imita a interface pública da classe YOLO do Ultralytics:
    model = StubYOLOModel()
    results = model.predict(image_path, conf=0.25, iou=0.45)
    for r in results:
        for box in r.boxes:
            print(box["cls"], box["conf"], box["xyxy"])

Também fornece StubYOLOModel.from_file() para substituir YOLO("best.pt")
em código de produção durante testes unitários/de integração.
"""

from __future__ import annotations

import random
from pathlib import Path
from typing import Any


# ---------------------------------------------------------------------------
# Taxonomy — espelha dataset/data.yaml (32 classes)
# ---------------------------------------------------------------------------
CLASS_NAMES: dict[int, str] = {
    0:  "actor_user",
    1:  "actor_admin",
    2:  "edge_ddos_protection",
    3:  "edge_cdn",
    4:  "edge_waf",
    5:  "edge_gateway",
    6:  "edge_portal",
    7:  "external_entry_point",
    8:  "integration_orchestrator",
    9:  "integration_messaging",
    10: "compute_load_balancer",
    11: "compute_service",
    12: "compute_worker",
    13: "data_database",
    14: "data_cache",
    15: "data_storage",
    16: "security_identity_provider",
    17: "security_key_management",
    18: "obs_monitoring",
    19: "obs_audit",
    20: "external_backend_service",
    21: "external_saas_service",
    22: "external_web_service",
    23: "communication_service",
    24: "backup_service",
    25: "boundary_cloud",
    26: "boundary_region",
    27: "boundary_resource_group",
    28: "boundary_vpc_or_vnet",
    29: "boundary_subnet_public",
    30: "boundary_subnet_private",
    31: "boundary_autoscaling_group",
}

# Default detections returned when no fixture is set
_DEFAULT_BOXES: list[dict[str, Any]] = [
    {"cls": 0,  "conf": 0.92, "xyxy": [10,  10,  100, 100]},   # actor_user
    {"cls": 11, "conf": 0.87, "xyxy": [200, 50,  340, 130]},   # compute_service
    {"cls": 5,  "conf": 0.81, "xyxy": [120, 200, 260, 280]},   # edge_gateway
    {"cls": 13, "conf": 0.78, "xyxy": [350, 200, 490, 290]},   # data_database
    {"cls": 9,  "conf": 0.74, "xyxy": [200, 300, 340, 380]},   # integration_messaging
]


# ---------------------------------------------------------------------------
# Result / Boxes objects
# ---------------------------------------------------------------------------

class StubBox:
    """Mimics a single detection box from Ultralytics Results.boxes[i]."""

    def __init__(self, cls: int, conf: float, xyxy: list[float]) -> None:
        self._cls = cls
        self._conf = conf
        self._xyxy = xyxy

    # Attribute-style access (matches Ultralytics tensor-item interface)
    @property
    def cls(self) -> "StubTensor":
        return StubTensor(self._cls)

    @property
    def conf(self) -> "StubTensor":
        return StubTensor(self._conf)

    @property
    def xyxy(self) -> list[float]:
        return self._xyxy

    # Dict-style access (used by some wrapper code)
    def __getitem__(self, key: str) -> Any:
        return {"cls": self._cls, "conf": self._conf, "xyxy": self._xyxy}[key]

    def __repr__(self) -> str:
        name = CLASS_NAMES.get(self._cls, f"cls_{self._cls}")
        return f"StubBox(cls={self._cls} '{name}', conf={self._conf:.2f}, xyxy={self._xyxy})"


class StubTensor:
    """Thin wrapper that mimics .item() on a 0-d torch tensor."""

    def __init__(self, value: float | int) -> None:
        self._value = value

    def item(self) -> float | int:
        return self._value

    def __float__(self) -> float:
        return float(self._value)

    def __int__(self) -> int:
        return int(self._value)

    def __repr__(self) -> str:
        return f"StubTensor({self._value})"


class StubResult:
    """Mimics a single Ultralytics Results object returned by model.predict()."""

    def __init__(
        self,
        boxes: list[dict[str, Any]] | None = None,
        image_path: str = "",
    ) -> None:
        raw = boxes if boxes is not None else _DEFAULT_BOXES
        self.boxes: list[StubBox] = [
            StubBox(b["cls"], b["conf"], b["xyxy"]) for b in raw
        ]
        self.path = image_path
        # Expose names dict (mirrors Ultralytics Results.names)
        self.names = CLASS_NAMES

    def __len__(self) -> int:
        return len(self.boxes)

    def __repr__(self) -> str:
        return f"StubResult(path='{self.path}', boxes={len(self.boxes)})"


# ---------------------------------------------------------------------------
# Stub model
# ---------------------------------------------------------------------------

class StubYOLOModel:
    """
    Drop-in stub for ultralytics.YOLO.

    Usage in tests
    --------------
    import pytest
    from tests.mocks.stub_model import StubYOLOModel

    @pytest.fixture
    def yolo_model():
        return StubYOLOModel()

    # Or with a fixed set of detections:
    @pytest.fixture
    def yolo_model_with_boxes():
        boxes = [{"cls": 13, "conf": 0.95, "xyxy": [50, 50, 200, 150]}]
        return StubYOLOModel(fixed_boxes=boxes)
    """

    def __init__(
        self,
        model_path: str = "stub",
        fixed_boxes: list[dict[str, Any]] | None = None,
        seed: int = 42,
    ) -> None:
        self.model_path = model_path
        self._fixed_boxes = fixed_boxes
        self._rng = random.Random(seed)
        # Public attributes that production code may read
        self.names = CLASS_NAMES

    @classmethod
    def from_file(cls, path: str | Path, **kwargs: Any) -> "StubYOLOModel":
        """Factory method — replaces YOLO('best.pt') in tests."""
        return cls(model_path=str(path), **kwargs)

    # ------------------------------------------------------------------
    # Predict
    # ------------------------------------------------------------------

    def predict(
        self,
        source: str | Path,
        conf: float = 0.25,
        iou: float = 0.45,
        imgsz: int = 640,
        verbose: bool = False,
        **kwargs: Any,
    ) -> list[StubResult]:
        """
        Return a list with one StubResult per image source provided.

        If `fixed_boxes` was supplied at construction, those boxes are always
        returned (after filtering by `conf`).  Otherwise a small deterministic
        set of default boxes is returned.
        """
        sources = [source] if isinstance(source, (str, Path)) else list(source)
        results: list[StubResult] = []

        for src in sources:
            boxes = self._fixed_boxes if self._fixed_boxes is not None else _DEFAULT_BOXES
            # Apply confidence threshold (mirrors real model behaviour)
            filtered = [b for b in boxes if b["conf"] >= conf]
            results.append(StubResult(boxes=filtered, image_path=str(src)))

        return results

    # ------------------------------------------------------------------
    # Val  (returns a minimal metrics stub)
    # ------------------------------------------------------------------

    def val(self, **kwargs: Any) -> "StubMetrics":
        return StubMetrics()

    # ------------------------------------------------------------------
    # Export (no-op — returns a fake path)
    # ------------------------------------------------------------------

    def export(self, format: str = "onnx", **kwargs: Any) -> str:
        fake_path = str(Path(self.model_path).with_suffix(f".{format}"))
        return fake_path

    def __repr__(self) -> str:
        return f"StubYOLOModel(path='{self.model_path}')"


# ---------------------------------------------------------------------------
# Stub metrics (for .val() calls in tests)
# ---------------------------------------------------------------------------

class StubBoxMetrics:
    """Mimics ultralytics.utils.metrics.DetMetrics.box."""
    map50: float = 0.82
    map: float = 0.61       # mAP@0.5:0.95
    mp: float = 0.85        # mean precision
    mr: float = 0.79        # mean recall


class StubMetrics:
    """Mimics the object returned by model.val()."""
    box = StubBoxMetrics()

    def __repr__(self) -> str:
        return (
            f"StubMetrics(mAP@0.5={self.box.map50}, "
            f"mAP@0.5:0.95={self.box.map})"
        )
