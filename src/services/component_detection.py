"""Serviço de detecção de componentes de arquitetura (Spec 003)."""

from pathlib import Path
from uuid import uuid4

from src.core.logging import get_logger
from src.domain.models import (
    ArchitectureGraph,
    BoundingBox,
    DataFlow,
    DetectedComponent,
    Point,
)

logger = get_logger(__name__)


class ComponentDetectionService:
    """Serviço de detecção de componentes usando YOLOv11n."""

    def __init__(self, model_path: str | None = None):
        """Inicializa o serviço de detecção.

        Args:
            model_path: Caminho para o modelo YOLO (.pt ou .onnx).
                         Se None ou arquivo não existir, usa modo mock.
        """
        self.model_path = model_path
        self.model = None
        self._load_model()

    def _load_model(self) -> None:
        """Carrega o modelo YOLO se disponível."""
        if self.model_path and Path(self.model_path).exists():
            try:
                from ultralytics import YOLO

                self.model = YOLO(self.model_path)
                logger.info(f"Modelo YOLO carregado de {self.model_path}")
            except Exception as e:
                logger.warning(f"Falha ao carregar modelo YOLO: {e}. Usando modo mock.")
                self.model = None
        else:
            logger.info("Modelo YOLO não encontrado. Usando modo mock.")

    async def detect(self, image_path: str | Path) -> ArchitectureGraph:
        """Detecta componentes em uma imagem de diagrama.

        Args:
            image_path: Caminho para a imagem.

        Returns:
            ArchitectureGraph: Grafo de arquitetura detectado.
        """
        image_path = Path(image_path)

        if not image_path.exists():
            raise FileNotFoundError(f"Imagem não encontrada: {image_path}")

        # Se tem modelo YOLO, usa inferência real
        if self.model:
            return await self._detect_with_yolo(image_path)

        # Modo mock: retorna componentes simulados para testes
        return await self._detect_mock(image_path)

    async def _detect_with_yolo(self, image_path: Path) -> ArchitectureGraph:
        """Executa detecção com modelo YOLO real."""
        # TODO: Implementar inferência real quando modelo estiver treinado (Spec 002)
        # Por enquanto, retorna mock
        logger.info("Usando detecção mock (modelo YOLO não treinado ainda)")
        return await self._detect_mock(image_path)

    async def _detect_mock(self, image_path: Path) -> ArchitectureGraph:
        """Retorna componentes mock para desenvolvimento.

        Simula a detecção de um diagrama típico:
        - Usuario (esquerda)
        - API (centro)
        - Banco de dados (direita)
        """
        logger.info(f"Detectando componentes mock em {image_path.name}")

        # Criar componentes fictícios (simulando um diagrama de 3 camadas)
        user_id = str(uuid4())
        api_id = str(uuid4())
        db_id = str(uuid4())

        components = [
            DetectedComponent(
                id=user_id,
                type="user",
                confidence=0.95,
                bbox=BoundingBox(x_min=50, y_min=150, x_max=120, y_max=220),
                center=Point(x=85, y=185),
            ),
            DetectedComponent(
                id=api_id,
                type="api",
                confidence=0.91,
                bbox=BoundingBox(x_min=250, y_min=130, x_max=350, y_max=230),
                center=Point(x=300, y=180),
            ),
            DetectedComponent(
                id=db_id,
                type="database",
                confidence=0.88,
                bbox=BoundingBox(x_min=480, y_min=140, x_max=560, y_max=220),
                center=Point(x=520, y=180),
            ),
        ]

        # Inferir fluxos de dados baseado na proximidade espacial
        data_flows = [
            DataFlow(
                source_id=user_id,
                target_id=api_id,
                direction="unidirectional",
                inferred=True,
            ),
            DataFlow(
                source_id=api_id,
                target_id=db_id,
                direction="bidirectional",
                inferred=True,
            ),
        ]

        # Trust boundaries: agrupar por zona
        trust_boundaries = [
            [user_id],  # Zona pública (Internet)
            [api_id],   # Zona de fronteira (DMZ/API)
            [db_id],    # Zona privada (Data Layer)
        ]

        return ArchitectureGraph(
            components=components,
            data_flows=data_flows,
            trust_boundaries=trust_boundaries,
        )

    def is_mock_mode(self) -> bool:
        """Retorna True se está operando em modo mock (sem modelo YOLO)."""
        return self.model is None
