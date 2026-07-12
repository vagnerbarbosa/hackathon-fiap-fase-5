"""Analisador heurístico de relacionamentos para componentes de arquitetura.

Infere data flows e trust boundaries baseado em posições espaciais.
"""

import logging
from dataclasses import dataclass
from typing import List, Tuple

from src.domain.models import DataFlow, DetectedComponent

logger = logging.getLogger(__name__)


@dataclass
class ProximityResult:
    """Resultado de verificação de proximidade entre dois componentes."""

    source_id: str
    target_id: str
    distance: float
    aligned: bool


class RelationshipAnalyzer:
    """Analisa relacionamentos espaciais entre componentes detectados.

    Usa heurísticas para inferir:
    - Data Flows: componentes próximos e alinhados
    - Trust Boundaries: grupos por tipo de componente

    Usage:
        >>> analyzer = RelationshipAnalyzer(proximity_threshold=150)
        >>> flows = analyzer.infer_data_flows(components)
        >>> boundaries = analyzer.infer_trust_boundaries(components)
    """

    def __init__(
        self,
        proximity_threshold: float = 150.0,
        alignment_tolerance: float = 50.0,
    ):
        """Inicializa o analisador.

        Args:
            proximity_threshold: Distância máxima (pixels) para inferência de flow.
            alignment_tolerance: Tolerância para alinhamento horizontal/vertical.
        """
        self.proximity_threshold = proximity_threshold
        self.alignment_tolerance = alignment_tolerance

    def infer_data_flows(
        self,
        components: List[DetectedComponent],
    ) -> List[DataFlow]:
        """Infere data flows baseado na proximidade dos componentes.

        Cria flows entre componentes que estão:
        1. Dentro da distância proximity_threshold
        2. Alinhados horizontalmente ou verticalmente

        Args:
            components: Lista de componentes detectados.

        Returns:
            Lista de objetos DataFlow inferidos.
        """
        if len(components) < 2:
            return []

        flows = []
        processed_pairs = set()

        for i, source in enumerate(components):
            for target in components[i + 1 :]:
                # Avoid duplicate pairs
                pair = tuple(sorted([source.id, target.id]))
                if pair in processed_pairs:
                    continue
                processed_pairs.add(pair)

                # Check proximity
                distance = self._compute_distance(source, target)
                if distance > self.proximity_threshold:
                    continue

                # Check alignment
                aligned = self._is_aligned(source, target)
                if not aligned:
                    continue

                # Determine direction
                direction = self._infer_direction(source, target)

                flow = DataFlow(
                    source_id=source.id,
                    target_id=target.id,
                    direction=direction,
                    inferred=True,
                )
                flows.append(flow)

                logger.debug(
                    f"Inferred flow: {source.type} -> {target.type} "
                    f"(distance={distance:.1f}px)"
                )

        logger.info(f"Inferred {len(flows)} data flows from {len(components)} components")
        return flows

    def infer_trust_boundaries(
        self,
        components: List[DetectedComponent],
    ) -> List[List[str]]:
        """Agrupa componentes em trust boundaries por tipo.

        Regras:
        - "user", "mobile_app" -> Zona pública
        - "api", "web_server" -> DMZ/Frontend
        - "database", "cache", "storage", "queue" -> Camada privada/dados
        - "external_service" -> Zona externa
        - "container" -> Depende do contexto (agrupado por proximidade)

        Args:
            components: Lista de componentes detectados.

        Returns:
            Lista de grupos de IDs de componentes (trust boundaries).
        """
        if not components:
            return []

        # Define zone mapping
        zones = {
            "public": ["user", "mobile_app"],
            "dmz": ["api", "web_server"],
            "private": ["database", "cache", "storage", "queue"],
            "external": ["external_service"],
            "dynamic": ["container"],
        }

        # Group by zone
        public_ids = []
        dmz_ids = []
        private_ids = []
        external_ids = []
        dynamic = []

        for comp in components:
            if comp.type in zones["public"]:
                public_ids.append(comp.id)
            elif comp.type in zones["dmz"]:
                dmz_ids.append(comp.id)
            elif comp.type in zones["private"]:
                private_ids.append(comp.id)
            elif comp.type in zones["external"]:
                external_ids.append(comp.id)
            else:
                dynamic.append(comp)

        # Group dynamic components (containers) by proximity
        dynamic_groups = self._group_by_proximity(dynamic)

        # Build boundaries
        boundaries = []
        if public_ids:
            boundaries.append(public_ids)
        if dmz_ids:
            boundaries.append(dmz_ids)
        if private_ids:
            boundaries.append(private_ids)
        if external_ids:
            boundaries.append(external_ids)
        boundaries.extend(dynamic_groups)

        logger.info(f"Inferred {len(boundaries)} trust boundaries")
        return boundaries

    def _compute_distance(
        self,
        comp1: DetectedComponent,
        comp2: DetectedComponent,
    ) -> float:
        """Calcula distância euclidiana entre centros de componentes.

        Args:
            comp1: Primeiro componente.
            comp2: Segundo componente.

        Returns:
            Distância em pixels.
        """
        dx = comp1.center.x - comp2.center.x
        dy = comp1.center.y - comp2.center.y
        return (dx**2 + dy**2) ** 0.5

    def _is_aligned(
        self,
        comp1: DetectedComponent,
        comp2: DetectedComponent,
    ) -> bool:
        """Verifica se componentes estão alinhados horizontalmente ou verticalmente.

        Args:
            comp1: Primeiro componente.
            comp2: Segundo componente.

        Returns:
            True se alinhado dentro da tolerância.
        """
        # Check horizontal alignment (similar Y)
        dy = abs(comp1.center.y - comp2.center.y)
        if dy <= self.alignment_tolerance:
            return True

        # Check vertical alignment (similar X)
        dx = abs(comp1.center.x - comp2.center.x)
        if dx <= self.alignment_tolerance:
            return True

        return False

    def _infer_direction(
        self,
        source: DetectedComponent,
        target: DetectedComponent,
    ) -> str:
        """Infere direção do flow baseado nos tipos de componentes.

        Args:
            source: Componente fonte.
            target: Componente alvo.

        Returns:
            "unidirectional" or "bidirectional".
        """
        # User to anything is typically unidirectional (request)
        if source.type == "user":
            return "unidirectional"

        # External service to API is typically unidirectional (webhook)
        if source.type == "external_service" and target.type == "api":
            return "unidirectional"

        # Database with anything is typically bidirectional (read/write)
        if "database" in [source.type, target.type]:
            return "bidirectional"

        # Cache with API is bidirectional
        if "cache" in [source.type, target.type] and "api" in [
            source.type,
            target.type,
        ]:
            return "bidirectional"

        # Default: bidirectional for service-to-service
        return "bidirectional"

    def _group_by_proximity(
        self,
        components: List[DetectedComponent],
    ) -> List[List[str]]:
        """Agrupa componentes por proximidade espacial.

        Clustering simples: se dentro do limiar, mesmo grupo.

        Args:
            components: Lista de componentes para agrupar.

        Returns:
            Lista de grupos de IDs de componentes.
        """
        if not components:
            return []

        groups = []
        assigned = set()

        for comp in components:
            if comp.id in assigned:
                continue

            # Start new group
            group = [comp.id]
            assigned.add(comp.id)

            # Find neighbors
            for other in components:
                if other.id in assigned:
                    continue

                distance = self._compute_distance(comp, other)
                if distance <= self.proximity_threshold * 2:  # Larger threshold
                    group.append(other.id)
                    assigned.add(other.id)

            groups.append(group)

        return groups
