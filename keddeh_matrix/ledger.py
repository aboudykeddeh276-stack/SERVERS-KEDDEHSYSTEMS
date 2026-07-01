"""
Singular Observer Booted-State Ledger

The global ledger that maintains the permanent "booted state" of the
entire emulated server warehouse.

Under the Keddeh Matrix, every defined node relationship is pre-resolved
and recorded in this ledger. The warehouse operates in a permanent booted
state: when data transfers occur, the interaction does not travel linearly
through an artificial zero gap. Instead, routing registers as an immediate,
instantaneous boundary crossing relative to the Singular Observer's perspective.

The ledger acts as the single universally synced matrix of pre-resolved
KEX calculations built entirely on registered "1 wholes".
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Optional

from keddeh_matrix.core import KeddehMatrix
from keddeh_matrix.kex_seed import KEXSeed
from keddeh_matrix.mesh_routing import FormulaOfPerspectiveRouter, MeshNode


class LedgerError(Exception):
    """Raised when a ledger operation fails."""


@dataclass
class LedgerEntry:
    """A single entry in the Singular Observer ledger."""

    source_node_id: str
    target_node_id: str
    measured_perspective: int
    mirror_crossing: bool
    routing_mode: str
    resolved_at: float = field(default_factory=time.time)


class SingularObserverLedger:
    """
    The Singular Observer Booted-State Ledger.

    Maintains a pre-resolved record of all KEX routing calculations.
    When a node needs to communicate with another, it references this
    ledger instead of dynamically calculating paths through a void.

    The ledger ensures the warehouse is always in a "booted state" --
    every possible route is already resolved.
    """

    def __init__(self) -> None:
        self._entries: dict[tuple[str, str], LedgerEntry] = {}
        self._router = FormulaOfPerspectiveRouter()
        self._seeds: dict[str, KEXSeed] = {}
        self._booted: bool = False

    def register_node(self, seed: KEXSeed) -> None:
        """
        Register a KEX seed node in the ledger.

        The node is added to both the seed registry and the mesh router.
        """
        if seed.node_id in self._seeds:
            raise LedgerError(
                f"Node {seed.node_id!r} already registered in ledger."
            )
        self._seeds[seed.node_id] = seed
        mesh_node = MeshNode(
            node_id=seed.node_id, matrix_position=seed.matrix_position
        )
        self._router.register_node(mesh_node)
        self._booted = False  # New node invalidates boot state

    def boot(self) -> int:
        """
        Boot the ledger: pre-resolve all pairwise routing relationships.

        Returns the number of routes resolved. After booting, all routes
        are instantly accessible without dynamic calculation.
        """
        node_ids = list(self._seeds.keys())
        resolved_count = 0

        for i, source_id in enumerate(node_ids):
            for target_id in node_ids[i + 1 :]:
                # Resolve in both directions
                for src, tgt in [(source_id, target_id), (target_id, source_id)]:
                    route = self._router.resolve_route(src, tgt)
                    entry = LedgerEntry(
                        source_node_id=src,
                        target_node_id=tgt,
                        measured_perspective=route["measured_perspective"],
                        mirror_crossing=route["mirror_crossing"],
                        routing_mode=route["routing_mode"],
                    )
                    self._entries[(src, tgt)] = entry
                    resolved_count += 1

        self._booted = True
        return resolved_count

    def lookup(self, source_id: str, target_id: str) -> LedgerEntry:
        """
        Look up a pre-resolved route in the ledger.

        This is an instantaneous operation -- no dynamic path calculation.
        The ledger must be booted first.
        """
        if not self._booted:
            raise LedgerError(
                "Ledger is not booted. Call boot() to pre-resolve all routes."
            )
        key = (source_id, target_id)
        if key not in self._entries:
            raise LedgerError(
                f"Route {source_id!r} -> {target_id!r} not found in ledger."
            )
        return self._entries[key]

    @property
    def is_booted(self) -> bool:
        """True if the ledger is in the booted state."""
        return self._booted

    @property
    def entry_count(self) -> int:
        """Number of pre-resolved routing entries."""
        return len(self._entries)

    @property
    def node_count(self) -> int:
        """Number of registered nodes."""
        return len(self._seeds)

    def list_nodes(self) -> list[str]:
        """List all registered node IDs."""
        return list(self._seeds.keys())

    def all_entries(self) -> list[LedgerEntry]:
        """Return all ledger entries."""
        return list(self._entries.values())
