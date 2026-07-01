"""Tests for Formula of Perspective Mesh Routing."""

import pytest

from keddeh_matrix.core import KeddehMatrixError
from keddeh_matrix.mesh_routing import (
    FormulaOfPerspectiveRouter,
    MeshNode,
    MeshRoutingError,
)


class TestMeshNode:
    """Test mesh node creation."""

    def test_create_valid_node(self):
        node = MeshNode(node_id="rack_1", matrix_position=2)
        assert node.node_id == "rack_1"
        assert node.matrix_position == 2

    def test_reject_zero_position(self):
        with pytest.raises(KeddehMatrixError):
            MeshNode(node_id="rack_1", matrix_position=0)


class TestFormulaOfPerspectiveRouter:
    """Test the Formula of Perspective: X_measured = X_absolute - O."""

    def setup_method(self):
        self.router = FormulaOfPerspectiveRouter()
        self.router.register_node(MeshNode(node_id="A", matrix_position=1))
        self.router.register_node(MeshNode(node_id="B", matrix_position=3))
        self.router.register_node(MeshNode(node_id="C", matrix_position=-2))

    def test_perspective_from_origin(self):
        # X_measured = 3 - 1 = 2
        assert self.router.compute_perspective("A", "B") == 2

    def test_perspective_reverse(self):
        # X_measured = 1 - 3 = -2
        assert self.router.compute_perspective("B", "A") == -2

    def test_perspective_cross_boundary(self):
        # X_measured = -2 - 1 = -3
        assert self.router.compute_perspective("A", "C") == -3

    def test_perspective_same_position_projects_to_origin(self):
        # Register another node at position 1
        self.router.register_node(MeshNode(node_id="D", matrix_position=1))
        # X_measured = 1 - 1 = 0 -> projected to 1 (Singular Origin)
        assert self.router.compute_perspective("A", "D") == 1

    def test_mirror_crossing_detected(self):
        # A at +1, C at -2: different domains
        assert self.router.is_mirror_crossing("A", "C") is True

    def test_no_mirror_crossing_same_domain(self):
        # A at +1, B at +3: same domain
        assert self.router.is_mirror_crossing("A", "B") is False

    def test_resolve_route_structure(self):
        route = self.router.resolve_route("A", "C")
        assert route["observer"] == "A"
        assert route["target"] == "C"
        assert route["measured_perspective"] == -3
        assert route["mirror_crossing"] is True
        assert route["routing_mode"] == "instantaneous_boundary_crossing"

    def test_resolve_route_same_domain(self):
        route = self.router.resolve_route("A", "B")
        assert route["routing_mode"] == "direct_relational_access"

    def test_perspective_table(self):
        table = self.router.build_perspective_table("A")
        assert table["B"] == 2  # 3 - 1
        assert table["C"] == -3  # -2 - 1
        assert "A" not in table  # observer excluded

    def test_duplicate_registration_rejected(self):
        with pytest.raises(MeshRoutingError, match="already registered"):
            self.router.register_node(MeshNode(node_id="A", matrix_position=5))

    def test_unknown_node_lookup(self):
        with pytest.raises(MeshRoutingError, match="not found"):
            self.router.get_node("nonexistent")
