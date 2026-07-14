"""Testes unitários para RelationshipAnalyzer.

Testa heurísticas espaciais para inferir data flows e trust boundaries.
"""

import pytest
from src.domain.models import DetectedComponent, BoundingBox, Point
from src.services.relationship_analyzer import RelationshipAnalyzer


class TestRelationshipAnalyzer:
    """Testes para RelationshipAnalyzer."""

    @pytest.fixture
    def analyzer(self):
        """Cria analyzer com configurações padrão."""
        return RelationshipAnalyzer(
            proximity_threshold=150.0,
            alignment_tolerance=50.0,
        )

    @pytest.fixture
    def horizontal_components(self):
        """Componentes alinhados horizontalmente (lado a lado)."""
        return [
            DetectedComponent(
                id="user-1",
                type="user",
                confidence=0.95,
                bbox=BoundingBox(x_min=10, y_min=50, x_max=60, y_max=100),
                center=Point(x=35, y=75),
            ),
            DetectedComponent(
                id="api-1",
                type="api",
                confidence=0.91,
                bbox=BoundingBox(x_min=120, y_min=50, x_max=180, y_max=120),
                center=Point(x=150, y=85),  # Distância ~115px do user (35,75)
            ),
            DetectedComponent(
                id="db-1",
                type="database",
                confidence=0.88,
                bbox=BoundingBox(x_min=250, y_min=60, x_max=320, y_max=140),
                center=Point(x=285, y=100),  # Distância ~135px do api (150,85)
            ),
        ]

    @pytest.fixture
    def vertical_components(self):
        """Componentes alinhados verticalmente (empilhados)."""
        return [
            DetectedComponent(
                id="web-1",
                type="web_server",
                confidence=0.92,
                bbox=BoundingBox(x_min=100, y_min=50, x_max=200, y_max=100),
                center=Point(x=150, y=75),
            ),
            DetectedComponent(
                id="api-1",
                type="api",
                confidence=0.91,
                bbox=BoundingBox(x_min=110, y_min=140, x_max=190, y_max=190),
                center=Point(x=150, y=165),  # Distância 90px do web (150,75)
            ),
        ]

    @pytest.fixture
    def isolated_components(self):
        """Componentes muito distantes para flows."""
        return [
            DetectedComponent(
                id="user-1",
                type="user",
                confidence=0.95,
                bbox=BoundingBox(x_min=10, y_min=50, x_max=60, y_max=100),
                center=Point(x=35, y=75),
            ),
            DetectedComponent(
                id="api-1",
                type="api",
                confidence=0.91,
                bbox=BoundingBox(x_min=1000, y_min=500, x_max=1100, y_max=600),
                center=Point(x=1050, y=550),
            ),
        ]

    def test_empty_components_returns_empty(self, analyzer):
        """Sem componentes deve retornar sem flows."""
        flows = analyzer.infer_data_flows([])
        assert flows == []

    def test_single_component_returns_empty(self, analyzer):
        """Componente único não deve ter flows."""
        comp = DetectedComponent(
            id="user-1",
            type="user",
            confidence=0.95,
            bbox=BoundingBox(x_min=10, y_min=50, x_max=60, y_max=100),
            center=Point(x=35, y=75),
        )
        flows = analyzer.infer_data_flows([comp])
        assert flows == []

    def test_horizontal_alignment_creates_flows(self, analyzer, horizontal_components):
        """Componentes alinhados horizontalmente devem criar flows."""
        flows = analyzer.infer_data_flows(horizontal_components)

        # Deve criar flows entre componentes adjacentes
        assert len(flows) == 2

        # Verifica direções dos flows
        source_ids = [f.source_id for f in flows]
        assert "user-1" in source_ids
        assert "api-1" in source_ids

        # Todos os flows devem ser marcados como inferred
        assert all(f.inferred for f in flows)

    def test_vertical_alignment_creates_flows(self, analyzer, vertical_components):
        """Componentes alinhados verticalmente devem criar flows."""
        flows = analyzer.infer_data_flows(vertical_components)

        assert len(flows) == 1
        assert flows[0].source_id == "web-1"
        assert flows[0].target_id == "api-1"
        assert flows[0].inferred is True

    def test_isolated_components_no_flows(self, analyzer, isolated_components):
        """Componentes muito distantes não devem criar flows."""
        flows = analyzer.infer_data_flows(isolated_components)

        # Distância é muito grande (> proximity_threshold)
        assert len(flows) == 0

    def test_compute_distance(self, analyzer, horizontal_components):
        """Cálculo de distância entre componentes."""
        comp1 = horizontal_components[0]  # user em (35, 75)
        comp2 = horizontal_components[1]  # api em (150, 85)

        distance = analyzer._compute_distance(comp1, comp2)

        # Esperado: sqrt((150-35)^2 + (85-75)^2) = sqrt(115^2 + 10^2)
        expected = ((150 - 35) ** 2 + (85 - 75) ** 2) ** 0.5
        assert abs(distance - expected) < 0.001

    def test_is_aligned_horizontal(self, analyzer, horizontal_components):
        """Componentes com Y similar são alinhados horizontalmente."""
        comp1 = horizontal_components[0]  # Y = 75
        comp2 = horizontal_components[1]  # Y = 85

        assert analyzer._is_aligned(comp1, comp2) is True

    def test_is_aligned_vertical(self, analyzer, vertical_components):
        """Componentes com X similar são alinhados verticalmente."""
        comp1 = vertical_components[0]  # X = 150
        comp2 = vertical_components[1]  # X = 150

        assert analyzer._is_aligned(comp1, comp2) is True

    def test_not_aligned(self, analyzer, isolated_components):
        """Componentes distantes em X e Y não estão alinhados."""
        comp1 = isolated_components[0]
        comp2 = isolated_components[1]

        assert analyzer._is_aligned(comp1, comp2) is False


class TestTrustBoundaries:
    """Testes para inferência de trust boundaries."""

    @pytest.fixture
    def analyzer(self):
        """Cria analyzer."""
        return RelationshipAnalyzer()

    @pytest.fixture
    def mixed_components(self):
        """Componentes de diferentes tipos."""
        return [
            DetectedComponent(
                id="user-1",
                type="user",
                confidence=0.95,
                bbox=BoundingBox(x_min=10, y_min=50, x_max=60, y_max=100),
                center=Point(x=35, y=75),
            ),
            DetectedComponent(
                id="api-1",
                type="api",
                confidence=0.91,
                bbox=BoundingBox(x_min=200, y_min=50, x_max=300, y_max=120),
                center=Point(x=250, y=85),
            ),
            DetectedComponent(
                id="db-1",
                type="database",
                confidence=0.88,
                bbox=BoundingBox(x_min=400, y_min=60, x_max=500, y_max=140),
                center=Point(x=450, y=100),
            ),
            DetectedComponent(
                id="cache-1",
                type="cache",
                confidence=0.75,
                bbox=BoundingBox(x_min=420, y_min=200, x_max=480, y_max=260),
                center=Point(x=450, y=230),
            ),
            DetectedComponent(
                id="ext-1",
                type="external_service",
                confidence=0.70,
                bbox=BoundingBox(x_min=600, y_min=40, x_max=680, y_max=90),
                center=Point(x=640, y=65),
            ),
        ]

    def test_user_in_public_zone(self, analyzer, mixed_components):
        """Componentes user devem estar em zona pública."""
        boundaries = analyzer.infer_trust_boundaries(mixed_components)

        # Encontra boundary contendo user
        user_boundary = None
        for boundary in boundaries:
            if "user-1" in boundary:
                user_boundary = boundary
                break

        assert user_boundary is not None
        assert "user-1" in user_boundary

    def test_database_in_private_zone(self, analyzer, mixed_components):
        """Componentes database devem estar em zona privada."""
        boundaries = analyzer.infer_trust_boundaries(mixed_components)

        # Encontra boundary contendo database e cache (camada de dados)
        data_boundary = None
        for boundary in boundaries:
            if "db-1" in boundary:
                data_boundary = boundary
                break

        assert data_boundary is not None
        assert "db-1" in data_boundary

    def test_external_in_separate_zone(self, analyzer, mixed_components):
        """External services devem estar em sua própria zona."""
        boundaries = analyzer.infer_trust_boundaries(mixed_components)

        # Encontra boundary contendo external service
        ext_boundary = None
        for boundary in boundaries:
            if "ext-1" in boundary:
                ext_boundary = boundary
                break

        assert ext_boundary is not None
        assert len(ext_boundary) == 1  # Isolado

    def test_empty_components_no_boundaries(self, analyzer):
        """Sem componentes deve resultar em sem boundaries."""
        boundaries = analyzer.infer_trust_boundaries([])
        assert boundaries == []


class TestFlowDirection:
    """Testes para inferência de direção de flow."""

    @pytest.fixture
    def analyzer(self):
        return RelationshipAnalyzer()

    def test_user_to_api_is_unidirectional(self, analyzer):
        """Flow de user para API é tipicamente unidirecional (request)."""
        from src.domain.models import DataFlow

        user = DetectedComponent(
            id="user-1", type="user", confidence=0.95,
            bbox=BoundingBox(x_min=10, y_min=50, x_max=60, y_max=100),
            center=Point(x=35, y=75),
        )
        api = DetectedComponent(
            id="api-1", type="api", confidence=0.91,
            bbox=BoundingBox(x_min=200, y_min=50, x_max=300, y_max=120),
            center=Point(x=250, y=85),
        )

        direction = analyzer._infer_direction(user, api)
        assert direction == "unidirectional"

    def test_api_to_database_is_bidirectional(self, analyzer):
        """Flow entre API e database é tipicamente bidirecional."""
        api = DetectedComponent(
            id="api-1", type="api", confidence=0.91,
            bbox=BoundingBox(x_min=200, y_min=50, x_max=300, y_max=120),
            center=Point(x=250, y=85),
        )
        db = DetectedComponent(
            id="db-1", type="database", confidence=0.88,
            bbox=BoundingBox(x_min=400, y_min=60, x_max=500, y_max=140),
            center=Point(x=450, y=100),
        )

        direction = analyzer._infer_direction(api, db)
        assert direction == "bidirectional"

    def test_api_to_cache_is_bidirectional(self, analyzer):
        """Flow entre API e cache é bidirecional."""
        api = DetectedComponent(
            id="api-1", type="api", confidence=0.91,
            bbox=BoundingBox(x_min=200, y_min=50, x_max=300, y_max=120),
            center=Point(x=250, y=85),
        )
        cache = DetectedComponent(
            id="cache-1", type="cache", confidence=0.75,
            bbox=BoundingBox(x_min=350, y_min=200, x_max=420, y_max=260),
            center=Point(x=385, y=230),
        )

        direction = analyzer._infer_direction(api, cache)
        assert direction == "bidirectional"
