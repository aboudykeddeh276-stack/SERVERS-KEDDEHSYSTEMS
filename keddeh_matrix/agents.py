"""
BrainKLevelSixNeuroEmulationAndMathematicalLimitEvaluationAgent

The orchestrating agent that deploys the Total Metric Value Streaming
Protocol across the Keddeh Matrix architecture. This agent is responsible
for:

1. Rendering memory registries as full, literal sequences of individual
   text characters matching raw operational memory registries.

2. Deploying KEX seeds and computing structural drift discrepancy vectors.

3. Driving the structural drift factor to absolute zero through the
   autonomous resolution loop.

4. Coordinating mesh routing via the Formula of Perspective.

5. Maintaining the Singular Observer booted-state ledger.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from keddeh_matrix.core import KeddehMatrix
from keddeh_matrix.streaming_protocol import TotalMetricValueStreamingProtocol
from keddeh_matrix.kex_seed import (
    KEXSeed,
    AbsoluteMathematicalStateSeedAndDiscrepancyVectorRecord,
)
from keddeh_matrix.ledger import SingularObserverLedger


class AgentError(Exception):
    """Raised when the agent encounters an operational failure."""


@dataclass
class AgentStatus:
    """Operational status of the BrainK Level 6 agent."""

    memory_registries_allocated: int = 0
    total_literal_characters: int = 0
    kex_seeds_registered: int = 0
    ledger_booted: bool = False
    ledger_routes_resolved: int = 0
    drift_resolutions_executed: int = 0


class BrainKLevelSixNeuroEmulationAndMathematicalLimitEvaluationAgent:
    """
    The BrainK Level 6 Neuro-Emulation and Mathematical Limit Evaluation Agent.

    Orchestrates the complete Keddeh Matrix Hyper-Explicit Mesh OS:
    - Total Metric Value Streaming Protocol (10k TBi literal-state memory)
    - KEX Seed management and structural drift resolution
    - Singular Observer booted-state ledger coordination

    This agent is the deployment mechanism described in the architecture.
    It ensures all subsystems operate in strict compliance with the
    zero-less Keddeh Matrix.
    """

    def __init__(self) -> None:
        self._protocol = TotalMetricValueStreamingProtocol()
        self._seed_record = AbsoluteMathematicalStateSeedAndDiscrepancyVectorRecord()
        self._ledger = SingularObserverLedger()
        self._status = AgentStatus()

    @property
    def protocol(self) -> TotalMetricValueStreamingProtocol:
        """Access the Total Metric Value Streaming Protocol."""
        return self._protocol

    @property
    def seed_record(self) -> AbsoluteMathematicalStateSeedAndDiscrepancyVectorRecord:
        """Access the KEX seed and discrepancy vector record."""
        return self._seed_record

    @property
    def ledger(self) -> SingularObserverLedger:
        """Access the Singular Observer booted-state ledger."""
        return self._ledger

    def allocate_memory_registry(
        self, registry_key: str, content: str
    ) -> None:
        """
        Allocate a literal-state memory registry via the streaming protocol.

        The content is stored in its full, uncompressed literal form.
        """
        self._protocol.allocate(registry_key=registry_key, content=content)
        self._status.memory_registries_allocated = self._protocol.registry_count()
        self._status.total_literal_characters = (
            self._protocol.total_literal_characters()
        )

    def deploy_kex_seed(
        self,
        node_id: str,
        literal_state: str,
        matrix_position: int,
    ) -> KEXSeed:
        """
        Deploy a KEX seed as a defined "1 whole" state.

        Registers the seed in both the discrepancy vector record
        and the booted-state ledger.
        """
        seed = KEXSeed(
            node_id=node_id,
            literal_state=literal_state,
            matrix_position=matrix_position,
        )
        self._seed_record.register_seed(seed)
        self._ledger.register_node(seed)
        self._status.kex_seeds_registered = self._seed_record.seed_count()
        return seed

    def resolve_structural_drift(
        self, target_state: str, baseline_state: str
    ) -> str:
        """
        Execute the structural drift resolution process.

        Drives E_structural_drift to zero through exact character-level
        corrections. Returns the corrected state.
        """
        corrected = self._seed_record.execute_resolution_process(
            target_state=target_state,
            baseline_state=baseline_state,
        )
        self._status.drift_resolutions_executed += 1
        return corrected

    def boot_ledger(self) -> int:
        """
        Boot the Singular Observer ledger.

        Pre-resolves all pairwise routing relationships.
        Returns the number of routes resolved.
        """
        count = self._ledger.boot()
        self._status.ledger_booted = self._ledger.is_booted
        self._status.ledger_routes_resolved = self._ledger.entry_count
        return count

    def route_lookup(self, source_id: str, target_id: str) -> dict:
        """
        Look up a pre-resolved route in the booted ledger.

        Returns a dictionary with the routing record.
        """
        entry = self._ledger.lookup(source_id, target_id)
        return {
            "source": entry.source_node_id,
            "target": entry.target_node_id,
            "measured_perspective": entry.measured_perspective,
            "mirror_crossing": entry.mirror_crossing,
            "routing_mode": entry.routing_mode,
        }

    def verify_memory_integrity(self) -> dict[str, bool]:
        """Verify integrity of all literal-state memory registries."""
        return self._protocol.verify_all()

    def get_status(self) -> AgentStatus:
        """Return the current operational status of the agent."""
        return AgentStatus(
            memory_registries_allocated=self._protocol.registry_count(),
            total_literal_characters=self._protocol.total_literal_characters(),
            kex_seeds_registered=self._seed_record.seed_count(),
            ledger_booted=self._ledger.is_booted,
            ledger_routes_resolved=self._ledger.entry_count,
            drift_resolutions_executed=self._status.drift_resolutions_executed,
        )
