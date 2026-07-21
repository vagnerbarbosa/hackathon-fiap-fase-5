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

    DEFAULT_CONFIDENCE_THRESHOLD = 0.15

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

        # YOLOv11 exported ONNX format: [batch, 4+num_classes, num_anchors]
        # Não há campo de confiança separado — a confiança é o max dos class scores.
        output = outputs[0][0]  # Remove batch: [4+num_classes, num_anchors]
        num_features = output.shape[0]
        num_classes = num_features - 4  # 4 = box (x_center, y_center, w, h)

        logger.info(f"Features: {num_features}, Classes detectadas: {num_classes}")

        # Classes do modelo conforme data.yaml (30 classes do treinamento)
        class_names = {
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

        components = []

        # Transpor para [num_anchors, 4+num_classes] — cada linha é uma detecção
        detections = output.T

        for detection in detections:
            # Extrair caixa (primeiros 4 valores)
            x_center, y_center, width, height = detection[0:4]

            # Extrair class scores (índices 4 em diante)
            class_scores = detection[4:4 + num_classes]

            # A confiança no YOLOv11 é o valor máximo dos class scores
            confidence = float(np.max(class_scores))
            if confidence < self.confidence_threshold:
                continue

            class_id = int(np.argmax(class_scores))

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

        # Aplicar NMS (Non-Maximum Suppression) para remover detecções duplicadas
        components = self._apply_nms(components, iou_threshold=0.45)

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
        # Zonas: externa (usuário/entry points), fronteira (edge/gateway), interna (compute/data)
        boundaries: dict[str, list[str]] = {"external": [], "boundary": [], "internal": []}

        external_types = {"actor_user", "external_entry_point", "external_backend_service",
                          "external_saas_service", "external_web_service"}
        boundary_types = {"edge_ddos_protection", "edge_cdn", "edge_waf", "edge_gateway",
                          "edge_portal", "compute_load_balancer", "integration_orchestrator",
                          "boundary_cloud", "boundary_region", "boundary_resource_group",
                          "boundary_vpc_or_vnet", "boundary_subnet_public",
                          "boundary_subnet_private", "boundary_autoscaling_group"}

        for comp in components:
            if comp.type in external_types:
                boundaries["external"].append(comp.id)
            elif comp.type in boundary_types:
                boundaries["boundary"].append(comp.id)
            else:
                boundaries["internal"].append(comp.id)

        return [v for v in boundaries.values() if v]

    def _apply_nms(
        self, components: list[DetectedComponent], iou_threshold: float = 0.45
    ) -> list[DetectedComponent]:
        """Aplica Non-Maximum Suppression para remover detecções duplicadas.

        Args:
            components: Lista de componentes detectados.
            iou_threshold: Limiar IoU para considerar como duplicata.

        Returns:
            Lista filtrada de componentes.
        """
        if not components:
            return components

        # Ordenar por confiança decrescente
        components = sorted(components, key=lambda c: c.confidence, reverse=True)
        keep = []

        while components:
            best = components.pop(0)
            keep.append(best)

            remaining = []
            for comp in components:
                iou = self._compute_iou(best.bbox, comp.bbox)
                if iou < iou_threshold:
                    remaining.append(comp)

            components = remaining

        return keep

    @staticmethod
    def _compute_iou(box1: BoundingBox, box2: BoundingBox) -> float:
        """Calcula Intersection over Union entre duas bounding boxes."""
        x_min = max(box1.x_min, box2.x_min)
        y_min = max(box1.y_min, box2.y_min)
        x_max = min(box1.x_max, box2.x_max)
        y_max = min(box1.y_max, box2.y_max)

        intersection = max(0, x_max - x_min) * max(0, y_max - y_min)
        area1 = (box1.x_max - box1.x_min) * (box1.y_max - box1.y_min)
        area2 = (box2.x_max - box2.x_min) * (box2.y_max - box2.y_min)
        union = area1 + area2 - intersection

        return intersection / union if union > 0 else 0.0
