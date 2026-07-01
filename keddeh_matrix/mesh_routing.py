"""
Formula of Perspective Mesh Routing

Implements instantaneous mesh routing on the Keddeh Matrix.

Traditional overlay networks (BGP, OSPF, VXLAN) waste compute dynamically
updating B-tree routing tables and calculating vector paths against an
absolute (0,0) origin. Under the Keddeh Matrix, routing is calibrated
strictly by the Formula of Perspective:

    X_measured = X_absolute - O

Where O is the Singular Observer (the sending node). The observer is the
origin -- not an abstract Cartesian zero point.

The entire emulated server warehouse operates on a single universally
synced matrix ledger of pre-resolved KEX calculations. Edge virtual
routers do not perform heavy path calculations; they reference the
ledger as a translative lexicon, instantly accessing pre-registered
relational states.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from keddeh_matrix.core import KeddehMatrix


class MeshRoutingError(Exception):
    """Raised when a mesh routing operation fails."""


@dataclass(frozen=True)
class MeshNode:
    """
    A node in the Keddeh Mesh.

    Each node has a matrix_position (its absolute position in the
    Keddeh Matrix) and a node_id for identification.
    """

    node_id: str
    matrix_position: int

    def __post_init__(self) -> None:
        KeddehMatrix.validate(self.matrix_position)


class FormulaOfPerspectiveRouter:
    """
    Mesh router implementing the Formula of Perspective.

    X_measured = X_absolute - O

    Where:
    - X_measured: the measured position of the target from the observer
    - X_absolute: the absolute matrix position of the target node
    - O: the observer's matrix position (Singular Observer)

    Routing is instantaneous because all node relationships are
    pre-resolved in the global ledger. No dynamic path calculation
    through a Cartesian void is required.
    """

    def __init__(self) -> None:
        self._nodes: dict[str, MeshNode] = {}

    def register_node(self, node: MeshNode) -> None:
        """Register a node in the mesh."""
        if node.node_id in self._nodes:
            raise MeshRoutingError(
                f"Node {node.node_id!r} already registered in the mesh."
            )
        self._nodes[node.node_id] = node

    def get_node(self, node_id: str) -> MeshNode:
        """Retrieve a registered mesh node."""
        if node_id not in self._nodes:
            raise MeshRoutingError(f"Node {node_id!r} not found in mesh.")
        return self._nodes[node_id]

    def compute_perspective(
        self, observer_id: str, target_id: str
    ) -> int:
        """
        Compute the Formula of Perspective between two nodes.

        X_measured = X_absolute(target) - O(observer)

        The result is the relative position of the target from the
        observer's perspective. If the raw result would be zero
        (observer and target at same position), the Keddeh Matrix
        projects it to the Singular Origin.
        """
        observer = self.get_node(observer_id)
        target = self.get_node(target_id)

        raw_distance = target.matrix_position - observer.matrix_position
        return KeddehMatrix.project(raw_distance)

    def is_mirror_crossing(self, observer_id: str, target_id: str) -> bool:
        """
        Determine if routing between two nodes crosses the mirror boundary.

        A mirror crossing occurs when the observer is in one domain
        (positive/negative) and the target is in the other. Under
        the Keddeh Matrix, this crossing is instantaneous -- no
        traversal through a zero gap.
        """
        observer = self.get_node(observer_id)
        target = self.get_node(target_id)

        observer_positive = KeddehMatrix.is_positive_domain(observer.matrix_position)
        target_positive = KeddehMatrix.is_positive_domain(target.matrix_position)

        return observer_positive != target_positive

    def resolve_route(
        self, observer_id: str, target_id: str
    ) -> dict:
        """
        Resolve the complete routing record between two nodes.

        Returns a pre-resolved KEX routing record containing the
        perspective calculation, mirror crossing status, and
        structural metadata.
        """
        perspective = self.compute_perspective(observer_id, target_id)
        mirror = self.is_mirror_crossing(observer_id, target_id)
        observer = self.get_node(observer_id)
        target = self.get_node(target_id)

        return {
            "observer": observer.node_id,
            "target": target.node_id,
            "observer_position": observer.matrix_position,
            "target_position": target.matrix_position,
            "measured_perspective": perspective,
            "mirror_crossing": mirror,
            "boundary_distance_observer": KeddehMatrix.boundary_distance(
                observer.matrix_position
            ),
            "boundary_distance_target": KeddehMatrix.boundary_distance(
                target.matrix_position
            ),
            "routing_mode": "instantaneous_boundary_crossing"
            if mirror
            else "direct_relational_access",
        }

    def build_perspective_table(
        self, observer_id: str
    ) -> dict[str, int]:
        """
        Build a complete perspective table from a single observer.

        Returns a mapping of target_node_id -> measured_perspective
        for all nodes in the mesh as seen from the observer.
        """
        table = {}
        for node_id in self._nodes:
            if node_id != observer_id:
                table[node_id] = self.compute_perspective(observer_id, node_id)
        return table

    def list_nodes(self) -> list[str]:
        """List all registered node IDs."""
        return list(self._nodes.keys())

    def node_count(self) -> int:
        """Return the number of registered nodes."""
        return len(self._nodes)
