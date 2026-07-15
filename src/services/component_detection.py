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


class LowConfidenceError(Exception):
    """Exceção lançada quando nenhum componente é detectado com confiança suficiente."""

    def __init__(self, message: str = "Não foi possível detectar componentes na imagem"):
        self.message = message
        super().__init__(self.message)


class ModelNotLoadedError(Exception):
    """Exceção lançada quando o modelo ONNX não pode ser carregado."""

    def __init__(self, message: str = "Modelo de detecção não disponível"):
        self.message = message
        super().__init__(self.message)


class ComponentDetectionService:
    """Serviço de detecção de componentes usando YOLOv11n ONNX."""

    DEFAULT_CONFIDENCE_THRESHOLD = 0.3

    def __init__(
        self,
        model_path: str | None = None,
        confidence_threshold: float = DEFAULT_CONFIDENCE_THRESHOLD,
    ):
        """Inicializa o serviço de detecção.

        Args:
            model_path: Caminho para o modelo ONNX.
            confidence_threshold: Limiar mínimo de confiança (0.0-1.0).
                                  Componentes abaixo são descartados.

        Raises:
            ModelNotLoadedError: Se o modelo não for encontrado ou falhar ao carregar.
        """
        self.model_path = model_path
        self.confidence_threshold = confidence_threshold
        self.model = self._load_model()

    def _load_model(self):
        """Carrega o modelo ONNX.

        Returns:
            InferenceSession: Sessão ONNX carregada.

        Raises:
            ModelNotLoadedError: Se o modelo não for encontrado ou falhar ao carregar.
        """
        if not self.model_path:
            raise ModelNotLoadedError("Caminho do modelo não configurado")

        if not Path(self.model_path).exists():
            raise ModelNotLoadedError(
                f"Modelo ONNX não encontrado em: {self.model_path}. "
                "Certifique-se de que o arquivo best.onnx está disponível."
            )

        try:
            import onnxruntime as ort
            model = ort.InferenceSession(self.model_path)
            logger.info(f"Modelo ONNX carregado de {self.model_path}")
            return model
        except Exception as e:
            raise ModelNotLoadedError(
                f"Erro ao carregar modelo ONNX: {e}. "
                "Verifique se o arquivo best.onnx está correto."
            ) from e

    async def detect(self, image_path: str | Path) -> ArchitectureGraph:
        """Detecta componentes em uma imagem de diagrama.

        Args:
            image_path: Caminho para a imagem.

        Returns:
            ArchitectureGraph: Grafo de arquitetura detectado.

        Raises:
            LowConfidenceError: Se nenhum componente for detectado com
                               confiança suficiente.
            ModelNotLoadedError: Se o modelo não estiver disponível.
            FileNotFoundError: Se a imagem não for encontrada.
        """
        image_path = Path(image_path)

        if not image_path.exists():
            raise FileNotFoundError(f"Imagem não encontrada: {image_path}")

        return await self._detect_with_onnx(image_path)

    def _validate_confidence(self, components: list[DetectedComponent]) -> None:
        """Valida se há componentes com confiança suficiente.

        Args:
            components: Lista de componentes detectados.

        Raises:
            LowConfidenceError: Se nenhum componente atingir o threshold.
        """
        if not components:
            raise LowConfidenceError(
                "Nenhum componente detectado na imagem. "
                "Certifique-se de enviar um diagrama de arquitetura válido."
            )

        # Verificar se pelo menos um componente está acima do threshold
        max_confidence = max(c.confidence for c in components)
        if max_confidence < self.confidence_threshold:
            raise LowConfidenceError(
                f"Não foi possível detectar componentes devido à baixa confiança "
                f"(máx: {max_confidence:.2f}, mínimo esperado: {self.confidence_threshold:.2f}). "
                "Certifique-se de enviar um diagrama de arquitetura claro e válido."
            )

    async def _detect_with_onnx(self, image_path: Path) -> ArchitectureGraph:
        """Executa detecção com modelo ONNX."""
        import numpy as np
        import cv2

        logger.info(f"Executando inferência ONNX em {image_path.name}")

        # Carregar imagem
        image = cv2.imread(str(image_path))
        if image is None:
            raise ValueError(f"Não foi possível carregar imagem: {image_path}")

        original_height, original_width = image.shape[:2]

        # Pré-processamento YOLOv11
        input_size = 640
        image_resized = cv2.resize(image, (input_size, input_size))
        image_rgb = cv2.cvtColor(image_resized, cv2.COLOR_BGR2RGB)

        # Normalizar e preparar input [1, 3, 640, 640]
        input_tensor = image_rgb.astype(np.float32) / 255.0
        input_tensor = np.transpose(input_tensor, (2, 0, 1))
        input_tensor = np.expand_dims(input_tensor, axis=0)

        # Inferência
        input_name = self.model.get_inputs()[0].name
        outputs = self.model.run(None, {input_name: input_tensor})

        # Log do formato para debug
        logger.info(f"ONNX output shape: {outputs[0].shape}")

        # Processar detecções
        # Formato exportado: [batch, features, num_anchors]
        # features = 4(box) + 1(conf) + num_classes
        output = outputs[0][0]  # Remove batch: [features, num_anchors]
        num_features = output.shape[0]
        num_classes = num_features - 5  # 5 = 4(box) + 1(conf)

        logger.info(f"Features: {num_features}, Classes: {num_classes}")

        # Classes do modelo (do treinamento do Lucas)
        class_names = {
            0: "database",
            1: "queue",
            2: "api",
            3: "gateway",
            4: "client",
            5: "server",
            6: "web_server",
            7: "service",
        }

        components = []

        # O formato é [features, num_anchors] - precisamos transpor para [num_anchors, features]
        detections = output.T  # Agora cada linha é uma âncora

        for detection in detections:
            if len(detection) < 5 + min(1, num_classes):  # Precisa de pelo menos box + conf
                continue

            # Extrair confiança (índice 4)
            confidence = float(detection[4])
            if confidence < self.confidence_threshold:
                continue

            # Extrair caixa
            x_center, y_center, width, height = detection[0:4]

            # Extrair classe (índices após conf)
            class_scores = detection[5:5+num_classes]
            if len(class_scores) > 0:
                class_id = int(np.argmax(class_scores))
            else:
                class_id = 0

            # Converter para coordenadas da imagem original
            scale_x = original_width / input_size
            scale_y = original_height / input_size

            x_center_orig = x_center * scale_x
            y_center_orig = y_center * scale_y
            width_orig = width * scale_x
            height_orig = height * scale_y

            x_min = max(0, x_center_orig - width_orig / 2)
            y_min = max(0, y_center_orig - height_orig / 2)
            x_max = min(original_width, x_center_orig + width_orig / 2)
            y_max = min(original_height, y_center_orig + height_orig / 2)

            component = DetectedComponent(
                id=str(uuid4()),
                type=class_names.get(class_id, f"class_{class_id}"),
                confidence=float(confidence),
                bbox=BoundingBox(
                    x_min=int(x_min),
                    y_min=int(y_min),
                    x_max=int(x_max),
                    y_max=int(y_max),
                ),
                center=Point(
                    x=int(x_center_orig),
                    y=int(y_center_orig),
                ),
            )
            components.append(component)

        # Se nenhum componente detectado, lançar erro
        if not components:
            logger.warning("Nenhum componente detectado pelo modelo ONNX")
            raise LowConfidenceError(
                "Não foi possível detectar componentes na imagem. "
                "Certifique-se de enviar um diagrama de arquitetura válido com componentes claros."
            )

        logger.info(f"ONNX detectou {len(components)} componentes")

        # Criar data flows e trust boundaries
        data_flows = self._infer_data_flows(components)
        trust_boundaries = self._create_trust_boundaries(components)

        return ArchitectureGraph(
            components=components,
            data_flows=data_flows,
            trust_boundaries=trust_boundaries,
        )

    def _infer_data_flows(self, components: list[DetectedComponent]) -> list[DataFlow]:
        """Infere fluxos de dados baseado na proximidade espacial."""
        flows = []
        sorted_by_x = sorted(components, key=lambda c: c.center.x)

        for i in range(len(sorted_by_x) - 1):
            source = sorted_by_x[i]
            target = sorted_by_x[i + 1]

            flows.append(DataFlow(
                source_id=source.id,
                target_id=target.id,
                direction="unidirectional",
                inferred=True,
            ))

        return flows

    def _create_trust_boundaries(self, components: list[DetectedComponent]) -> list[list[str]]:
        """Cria trust boundaries baseado em zonas."""
        # Zonas: externa (usuário), fronteira (API), interna (database)
        boundaries: dict[str, list[str]] = {"external": [], "boundary": [], "internal": []}

        for comp in components:
            if comp.type in ["user"]:
                boundaries["external"].append(comp.id)
            elif comp.type in ["api", "gateway"]:
                boundaries["boundary"].append(comp.id)
            else:
                boundaries["internal"].append(comp.id)

        return [v for v in boundaries.values() if v]
