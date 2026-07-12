"""Stub/mock para modelo YOLO para habilitar desenvolvimento paralelo.

Este módulo fornece uma implementação mock da interface Ultralytics YOLO,
permitindo o desenvolvimento da Spec 003 sem aguardar a Spec 002 (treinamento do modelo).

Quando Lucas finalizar a Spec 002, substitua YOLOStub pelo modelo YOLO real.
"""

from dataclasses import dataclass, field
from typing import Any, List, Optional
from uuid import uuid4


@dataclass
class MockBox:
    """Mock da caixa de detecção YOLO."""

    cls: str  # nome da classe, ex: "user", "api", "database"
    conf: float  # confidence 0.0-1.0
    xyxy: List[float]  # [x_min, y_min, x_max, y_max]

    @property
    def xywh(self) -> List[float]:
        """Converte xyxy para xywh (centro x, centro y, largura, altura)."""
        x_min, y_min, x_max, y_max = self.xyxy
        w = x_max - x_min
        h = y_max - y_min
        x_center = x_min + w / 2
        y_center = y_min + h / 2
        return [x_center, y_center, w, h]


@dataclass
class MockResult:
    """Resultado mock YOLO contendo detecções."""

    boxes: List[MockBox] = field(default_factory=list)

    def __iter__(self):
        """Permite iteração sobre as caixas."""
        return iter(self.boxes)


class YOLOStub:
    """Implementação stub do modelo Ultralytics YOLO.

    Simula um modelo YOLOv11n treinado para detecção de componentes de arquitetura.
    Retorna detecções mock sem realizar inferência real.

    Uso:
        >>> from tests.mocks.yolo_stub import YOLOStub
        >>> model = YOLOStub("models/best.pt")
        >>> results = model.predict("image.jpg", conf=0.25)
        >>> for box in results[0].boxes:
        ...     print(f"{box.cls}: {box.conf:.2f}")
    """

    # Mapeamento de nomes de classes no nível da classe (label_id -> class_name)
    names = {
        0: "user",
        1: "web_server",
        2: "api",
        3: "database",
        4: "queue",
        5: "cache",
        6: "external_service",
        7: "mobile_app",
        8: "container",
        9: "storage",
    }

    def __init__(self, model_path: Optional[str] = None, task: Optional[str] = None):
        """Inicializa stub (sem carregamento real do modelo).

        Args:
            model_path: Ignorado no stub (para compatibilidade).
            task: Ignorado no stub (para compatibilidade).
        """
        self._model_path = model_path
        self._task = task or "detect"

    def predict(
        self,
        source: Any,
        conf: float = 0.25,
        iou: float = 0.45,
        imgsz: int = 640,
        **kwargs: Any,
    ) -> List[MockResult]:
        """Predição mock retornando detecções simuladas.

        Args:
            source: Caminho da imagem ou imagem PIL/numpy (ignorado no stub).
            conf: Limiar de confiança (filtrado no mock).
            iou: Limiar IoU para NMS (ignorado no stub).
            imgsz: Tamanho da imagem de entrada (ignorado no stub).
            **kwargs: Argumentos adicionais (ignorados no stub).

        Returns:
            List[MockResult]: Resultados de detecção simulados.
        """
        # Simula componentes típicos de diagrama de arquitetura
        mock_boxes = [
            MockBox(cls="user", conf=0.95, xyxy=[10.0, 50.0, 60.0, 100.0]),
            MockBox(cls="api", conf=0.91, xyxy=[200.0, 50.0, 300.0, 120.0]),
            MockBox(cls="database", conf=0.88, xyxy=[400.0, 60.0, 500.0, 140.0]),
            MockBox(cls="external_service", conf=0.72, xyxy=[600.0, 40.0, 680.0, 90.0]),
            MockBox(cls="cache", conf=0.65, xyxy=[350.0, 200.0, 420.0, 260.0]),
        ]

        # Filtra pelo limiar de confiança
        filtered_boxes = [b for b in mock_boxes if b.conf >= conf]

        return [MockResult(boxes=filtered_boxes)]

    def __call__(self, source: Any, **kwargs: Any) -> List[MockResult]:
        """Permite sintaxe model(source)."""
        return self.predict(source, **kwargs)


class YOLOWrapper:
    """Wrapper que tenta YOLO real, faz fallback para stub."""

    def __init__(self, model_path: str = "models/best.pt"):
        """Inicializa wrapper.

        Tenta carregar modelo YOLO real, faz fallback para stub se não disponível.

        Args:
            model_path: Caminho para arquivo do modelo (.pt ou .onnx).
        """
        self.model_path = model_path
        self._model = None
        self._using_stub = False

        self._load_model()

    def _load_model(self) -> None:
        """Tenta carregar modelo, faz fallback para stub."""
        try:
            from ultralytics import YOLO

            self._model = YOLO(self.model_path)
            self._using_stub = False
        except (ImportError, FileNotFoundError) as e:
            # Fallback to stub
            self._model = YOLOStub(self.model_path)
            self._using_stub = True
            print(f"[YOLOWrapper] Using stub (reason: {e})")

    @property
    def is_stub(self) -> bool:
        """Verifica se está usando implementação stub."""
        return self._using_stub

    @property
    def names(self) -> dict:
        """Obtém mapeamento de nomes de classes."""
        return self._model.names

    def predict(self, *args: Any, **kwargs: Any) -> Any:
        """Executa predição (delega para modelo ou stub)."""
        return self._model.predict(*args, **kwargs)

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        """Permite sintaxe model(source)."""
        return self._model(*args, **kwargs)


# Instâncias de conveniência para testes
stub_model = YOLOStub()
standard_mock_result = MockResult(
    boxes=[
        MockBox(cls="user", conf=0.95, xyxy=[10.0, 50.0, 60.0, 100.0]),
        MockBox(cls="api", conf=0.91, xyxy=[200.0, 50.0, 300.0, 120.0]),
        MockBox(cls="database", conf=0.88, xyxy=[400.0, 60.0, 500.0, 140.0]),
    ]
)
