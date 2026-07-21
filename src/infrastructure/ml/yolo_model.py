"""Wrapper do modelo YOLO para detecção de componentes.

Suporta formatos de modelo PyTorch (.pt) e ONNX (.onnx).
Fallback para implementação stub se arquivo de modelo não disponível.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, List, Optional, Union

import numpy as np

from src.core.config import settings

logger = logging.getLogger(__name__)


class DetectionResult:
    """Resultado de detecção normalizado do YOLO/ONNX."""

    def __init__(
        self,
        class_name: str,
        confidence: float,
        bbox: List[float],  # [x_min, y_min, x_max, y_max]
    ):
        self.class_name = class_name
        self.confidence = confidence
        self.bbox = bbox

    def __repr__(self) -> str:
        return f"DetectionResult({self.class_name}, {self.confidence:.2f})"


class YOLOModel:
    """Wrapper para modelo YOLO com suporte a formatos .pt e .onnx.

    Esta classe carrega um modelo YOLOv11 e fornece uma interface unificada
    para inferência. Suporta fallback para stub se modelo não disponível.

    Usage:
        >>> model = YOLOModel("models/best.pt")
        >>> results = model.predict("image.jpg", conf=0.25)
        >>> for det in results:
        ...     print(f"{det.class_name}: {det.confidence:.2f}")
    """

    _instance: Optional[YOLOModel] = None
    _model: Any = None
    _using_stub: bool = False
    _model_path: Optional[Path] = None
    _class_names: dict = {}

    def __new__(cls, model_path: Optional[str] = None) -> YOLOModel:
        """Padrão Singleton - garante que o modelo seja carregado apenas uma vez."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize(model_path)
        return cls._instance

    def _initialize(self, model_path: Optional[str] = None) -> None:
        """Inicializa o wrapper do modelo."""
        self._model_path = Path(model_path) if model_path else Path("models/best.pt")
        self._load_model()

    def _load_model(self) -> None:
        """Carrega modelo do arquivo ou faz fallback para stub."""
        if not self._model_path.exists():
            logger.warning(f"Model file not found: {self._model_path}")
            self._load_stub()
            return

        suffix = self._model_path.suffix.lower()

        try:
            if suffix == ".pt":
                self._load_pytorch()
            elif suffix == ".onnx":
                self._load_onnx()
            else:
                logger.warning(f"Unknown model format: {suffix}, using stub")
                self._load_stub()
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            self._load_stub()

    def _load_pytorch(self) -> None:
        """Carrega modelo YOLO PyTorch."""
        try:
            from ultralytics import YOLO

            self._model = YOLO(str(self._model_path))
            self._class_names = self._model.names
            self._using_stub = False
            logger.info(f"Loaded PyTorch YOLO model from {self._model_path}")
        except ImportError:
            logger.warning("ultralytics not installed, using stub")
            self._load_stub()

    def _load_onnx(self) -> None:
        """Carrega modelo ONNX."""
        try:
            import onnxruntime as ort

            # Configure providers (CUDA if available, else CPU)
            providers = ["CUDAExecutionProvider", "CPUExecutionProvider"]

            self._model = ort.InferenceSession(
                str(self._model_path),
                providers=providers,
            )
            self._using_stub = False

            # Load class names from metadata or config
            self._class_names = self._load_class_names()
            logger.info(f"Loaded ONNX model from {self._model_path}")
        except ImportError:
            logger.warning("onnxruntime not installed, using stub")
            self._load_stub()

    def _load_stub(self) -> None:
        """Carrega implementação stub para desenvolvimento."""
        # Import stub from local module (not tests) for production compatibility
        try:
            from tests.mocks.yolo_stub import YOLOStub
        except ImportError:
            # Fallback: define stub inline if tests not available
            from src.infrastructure.ml.yolo_stub import YOLOStub

        self._model = YOLOStub(str(self._model_path))
        self._class_names = self._model.names
        self._using_stub = True
        logger.info("Using YOLO stub (model not available)")

    def _load_class_names(self) -> dict:
        """Carrega mapeamento de nomes de classes (30 classes do treinamento)."""
        return {
            0: "actor_user",
            1: "edge_ddos_protection",
            2: "edge_cdn",
            3: "edge_waf",
            4: "edge_gateway",
            5: "edge_portal",
            6: "external_entry_point",
            7: "integration_orchestrator",
            8: "compute_load_balancer",
            9: "compute_service",
            10: "compute_worker",
            11: "data_database",
            12: "data_cache",
            13: "data_storage",
            14: "security_identity_provider",
            15: "security_key_management",
            16: "obs_monitoring",
            17: "obs_audit",
            18: "external_backend_service",
            19: "external_saas_service",
            20: "external_web_service",
            21: "communication_service",
            22: "backup_service",
            23: "boundary_cloud",
            24: "boundary_region",
            25: "boundary_resource_group",
            26: "boundary_vpc_or_vnet",
            27: "boundary_subnet_public",
            28: "boundary_subnet_private",
            29: "boundary_autoscaling_group",
        }

    @property
    def is_stub(self) -> bool:
        """Verifica se está usando implementação stub."""
        return self._using_stub

    @property
    def class_names(self) -> dict:
        """Obtém mapeamento de nomes de classes."""
        return self._class_names

    def predict(
        self,
        image: Union[str, Path, np.ndarray],
        conf: float = 0.15,
        iou: float = 0.45,
        imgsz: int = 640,
    ) -> List[DetectionResult]:
        """Executa inferência na imagem.

        Args:
            image: Caminho da imagem ou array numpy.
            conf: Limiar de confiança.
            iou: Limiar IoU para NMS.
            imgsz: Tamanho da imagem de entrada.

        Returns:
            Lista de DetectionResult com class_name, confidence, bbox.
        """
        if self._using_stub:
            return self._predict_stub(image, conf, iou, imgsz)

        # Check if PyTorch or ONNX model
        if hasattr(self._model, "predict"):
            return self._predict_pytorch(image, conf, iou, imgsz)
        else:
            return self._predict_onnx(image, conf, iou, imgsz)

    def _predict_stub(
        self,
        image: Union[str, Path, np.ndarray],
        conf: float,
        iou: float,
        imgsz: int,
    ) -> List[DetectionResult]:
        """Prediz usando stub."""
        results = self._model.predict(image, conf=conf, iou=iou, imgsz=imgsz)
        return self._parse_results(results)

    def _predict_pytorch(
        self,
        image: Union[str, Path, np.ndarray],
        conf: float,
        iou: float,
        imgsz: int,
    ) -> List[DetectionResult]:
        """Prediz usando YOLO PyTorch."""
        results = self._model.predict(
            source=image,
            conf=conf,
            iou=iou,
            imgsz=imgsz,
            verbose=False,
        )
        return self._parse_results(results)

    def _predict_onnx(
        self,
        image: Union[str, Path, np.ndarray],
        conf: float,
        iou: float,
        imgsz: int,
    ) -> List[DetectionResult]:
        """Prediz usando ONNX Runtime (formato YOLOv11)."""
        import cv2

        # Preprocess image
        if isinstance(image, (str, Path)):
            img = cv2.imread(str(image))
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        else:
            img = image

        original_h, original_w = img.shape[:2]

        # Resize and normalize
        img = cv2.resize(img, (imgsz, imgsz))
        img = img.astype(np.float32) / 255.0
        img = np.transpose(img, (2, 0, 1))  # HWC to CHW
        img = np.expand_dims(img, axis=0)  # Add batch dimension

        # Run inference
        input_name = self._model.get_inputs()[0].name
        outputs = self._model.run(None, {input_name: img})

        # Parse outputs (YOLOv11 format: [batch, 4+num_classes, num_anchors])
        return self._parse_onnx_outputs(outputs[0], conf, original_w, original_h, imgsz)

    def _parse_results(self, results: Any) -> List[DetectionResult]:
        """Analisa resultados YOLO em objetos DetectionResult."""
        detections = []

        for result in results:
            if hasattr(result, "boxes"):
                for box in result.boxes:
                    # Handle both stub (str) and real YOLO (int)
                    if isinstance(box.cls, str):
                        class_name = box.cls
                    else:
                        class_id = int(box.cls)
                        class_name = self._class_names.get(class_id, f"class_{class_id}")

                    confidence = float(box.conf)

                    # Handle xyxy attribute (could be list or tensor)
                    if hasattr(box, "xyxy"):
                        bbox = box.xyxy[0].tolist() if hasattr(box.xyxy, "tolist") else box.xyxy
                    else:
                        bbox = [0, 0, 0, 0]  # Fallback

                    detections.append(
                        DetectionResult(
                            class_name=class_name,
                            confidence=confidence,
                            bbox=bbox,
                        )
                    )

        return detections

    def _parse_onnx_outputs(
        self, output: np.ndarray, conf_threshold: float,
        original_w: int = 640, original_h: int = 640, imgsz: int = 640,
    ) -> List[DetectionResult]:
        """Analisa saídas do modelo ONNX no formato YOLOv11.

        YOLOv11 format: [batch, 4+num_classes, num_anchors]
        - Não há campo de confiança separado
        - A confiança é o valor máximo dos class scores
        """
        detections = []

        # output shape: [4+num_classes, num_anchors]
        data = output[0]  # Remove batch dimension
        num_features = data.shape[0]
        num_classes = num_features - 4

        scale_x = original_w / imgsz
        scale_y = original_h / imgsz

        # Transpor para [num_anchors, 4+num_classes]
        data = data.T

        for det in data:
            # Class scores começam no índice 4
            class_scores = det[4:4 + num_classes]
            confidence = float(np.max(class_scores))

            if confidence < conf_threshold:
                continue

            class_id = int(np.argmax(class_scores))
            class_name = self._class_names.get(class_id, f"class_{class_id}")

            # Convert from center format to corner format
            x_center, y_center, width, height = det[0:4]

            x_min = (x_center - width / 2) * scale_x
            y_min = (y_center - height / 2) * scale_y
            x_max = (x_center + width / 2) * scale_x
            y_max = (y_center + height / 2) * scale_y

            detections.append(
                DetectionResult(
                    class_name=class_name,
                    confidence=float(confidence),
                    bbox=[float(x_min), float(y_min), float(x_max), float(y_max)],
                )
            )

        return detections


class YOLOWrapper:
    """Wrapper de conveniência que fornece uma interface mais simples."""

    def __init__(self, model_path: Optional[str] = None):
        """Inicializa wrapper."""
        self.model = YOLOModel(model_path)

    def detect(
        self,
        image_path: Union[str, Path],
        conf: float = 0.25,
    ) -> List[DetectionResult]:
        """Detecta componentes na imagem.

        Args:
            image_path: Caminho para o arquivo de imagem.
            conf: Limiar de confiança.

        Returns:
            Lista de detecções.
        """
        return self.model.predict(image_path, conf=conf)

    @property
    def is_stub(self) -> bool:
        """Verifica se está usando stub."""
        return self.model.is_stub
