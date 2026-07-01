"""
KEX Seed: Absolute Mathematical State Seed and Discrepancy Vector Record

Implements the KEX (Keddeh EXchange) seed system for emulated VOLUME
networking.

Under the Keddeh Matrix, virtual server nodes are not instantiated from
a void. Each node is established as a distinct defined state -- a singular
"1 whole" KEX seed. The seed profiles the structural environment and
target network nodes without hex offsets.

The structural drift error vector measures exact character-level variances
between the target KEX seed and the mesh baseline:

    E_structural_drift = sum(CharacterMismatchCount(T_literal_state, M_keddeh_form))

The execution loop autonomously applies exact updates, driving drift to zero:

    lim k->inf (E_structural_drift - sum(ExecuteResolutionProcess(delta_i))) = 0
"""

from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass, field
from typing import Optional

from keddeh_matrix.core import KeddehMatrix, KeddehMatrixError


class KEXSeedError(Exception):
    """Raised when a KEX seed operation fails."""


@dataclass(frozen=True)
class KEXSeed:
    """
    A singular "1 whole" KEX seed.

    Represents a fully defined network node state in the Keddeh Matrix.
    No dynamic IP allocation, no hex MAC addresses -- the seed is the
    complete structural identity of the node.
    """

    node_id: str
    literal_state: str
    matrix_position: int
    created_at: float = field(default_factory=time.time)

    def __post_init__(self) -> None:
        KeddehMatrix.validate(self.matrix_position)
        if not self.node_id:
            raise KEXSeedError("Node ID must be a non-empty defined state.")

    @property
    def fingerprint(self) -> str:
        """Compute the structural fingerprint of this KEX seed."""
        payload = f"{self.node_id}:{self.literal_state}:{self.matrix_position}"
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    @property
    def character_count(self) -> int:
        """Total character count of the literal state."""
        return len(self.literal_state)


@dataclass
class DiscrepancyVector:
    """
    Records the structural drift between a target KEX seed and the
    mesh baseline.

    E_structural_drift = sum(CharacterMismatchCount(T_literal_state, M_keddeh_form))
    """

    target_state: str
    baseline_state: str
    mismatch_positions: list[int] = field(default_factory=list)
    mismatch_count: int = 0

    def __post_init__(self) -> None:
        self.mismatch_positions, self.mismatch_count = self._compute_drift()

    def _compute_drift(self) -> tuple[list[int], int]:
        """
        Compute character-level structural drift.

        Compares each character position between the target and baseline.
        Length differences are counted as additional mismatches.
        """
        positions = []
        max_len = max(len(self.target_state), len(self.baseline_state))
        min_len = min(len(self.target_state), len(self.baseline_state))

        for i in range(min_len):
            if self.target_state[i] != self.baseline_state[i]:
                positions.append(i)

        # Characters beyond the shorter string are all mismatches
        for i in range(min_len, max_len):
            positions.append(i)

        return positions, len(positions)

    @property
    def drift_factor(self) -> float:
        """
        The structural drift factor as a ratio.

        Returns 0.0 when target and baseline are identical (drift resolved).
        """
        max_len = max(len(self.target_state), len(self.baseline_state))
        if max_len == 0:
            return 0.0
        return self.mismatch_count / max_len

    @property
    def is_resolved(self) -> bool:
        """True when structural drift has been driven to zero."""
        return self.mismatch_count == 0


class AbsoluteMathematicalStateSeedAndDiscrepancyVectorRecord:
    """
    Manages KEX seeds and their structural drift resolution.

    Implements the autonomous execution loop that drives structural
    drift to absolute zero:

        lim k->inf (E_structural_drift - sum(ExecuteResolutionProcess(delta_i))) = 0

    Each resolution step applies exact character-level corrections,
    converging the target state to the mesh baseline without
    probabilistic approximation.
    """

    def __init__(self) -> None:
        self._seeds: dict[str, KEXSeed] = {}
        self._resolution_log: list[dict] = []

    def register_seed(self, seed: KEXSeed) -> None:
        """Register a KEX seed in the record."""
        if seed.node_id in self._seeds:
            raise KEXSeedError(
                f"KEX seed {seed.node_id!r} already registered as a defined state."
            )
        self._seeds[seed.node_id] = seed

    def get_seed(self, node_id: str) -> KEXSeed:
        """Retrieve a registered KEX seed."""
        if node_id not in self._seeds:
            raise KEXSeedError(f"KEX seed {node_id!r} not found in record.")
        return self._seeds[node_id]

    def compute_discrepancy(
        self, target_state: str, baseline_state: str
    ) -> DiscrepancyVector:
        """
        Compute the discrepancy vector between a target and baseline state.

        E_structural_drift = sum(CharacterMismatchCount(T, M))
        """
        return DiscrepancyVector(
            target_state=target_state, baseline_state=baseline_state
        )

    def execute_resolution_process(
        self, target_state: str, baseline_state: str, max_iterations: int = 1
    ) -> str:
        """
        Execute the resolution process to drive structural drift to zero.

        Applies exact character-level corrections to transform the target
        state into the baseline state. This is not a probabilistic
        approximation -- it is an exact structural correction.

        Returns the corrected state.
        """
        current_state = target_state

        for iteration in range(max_iterations):
            discrepancy = self.compute_discrepancy(current_state, baseline_state)

            if discrepancy.is_resolved:
                self._resolution_log.append({
                    "iteration": iteration,
                    "drift_factor": 0.0,
                    "status": "resolved",
                })
                break

            # Apply exact corrections: replace current with baseline at
            # each mismatch position. This is the delta_i resolution.
            corrected = list(current_state.ljust(len(baseline_state)))
            for pos in discrepancy.mismatch_positions:
                if pos < len(baseline_state):
                    corrected[pos] = baseline_state[pos]

            current_state = "".join(corrected[: len(baseline_state)])

            self._resolution_log.append({
                "iteration": iteration,
                "drift_factor": discrepancy.drift_factor,
                "mismatches_resolved": discrepancy.mismatch_count,
                "status": "correcting",
            })

        return current_state

    @property
    def resolution_log(self) -> list[dict]:
        """Return the full resolution process log."""
        return list(self._resolution_log)

    @property
    def registered_seeds(self) -> list[str]:
        """List all registered KEX seed node IDs."""
        return list(self._seeds.keys())

    def seed_count(self) -> int:
        """Return the number of registered seeds."""
        return len(self._seeds)
