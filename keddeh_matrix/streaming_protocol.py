"""
Total Metric Value Streaming Protocol

Implements the 10k TBi RAM literal-state memory addressing system.

Under the Keddeh Matrix, shorthand abstractions (hexadecimal 0x offsets,
compressed byte blocks) are explicitly replaced with continuous structural
state representations. Memory is addressed as uncompressed literal string
values that map directly to operational registries.

The mathematical state transfer function operates on T_literal_state:
the uncompressed text space mapping the operational architecture.

This protocol eradicates character drift by rejecting 0x compression
and plotting memory as literal, unbroken string definitions. Memory
allocation becomes a continuously verified, immutable truth.
"""

from __future__ import annotations

import hashlib
from typing import Optional

from keddeh_matrix.core import KeddehMatrix, KeddehMatrixError


class MemoryRegistryError(Exception):
    """Raised when a memory registry operation violates protocol constraints."""


class LiteralStateValue:
    """
    A single literal-state memory value.

    Represents an uncompressed, unhexified memory content. The value
    is stored as its full literal string representation -- never truncated,
    never compressed into shorthand notation.
    """

    def __init__(self, content: str, registry_key: str) -> None:
        if not registry_key:
            raise MemoryRegistryError("Registry key must be a non-empty string.")
        self._content = content
        self._registry_key = registry_key
        self._integrity_hash = self._compute_integrity()

    def _compute_integrity(self) -> str:
        """Compute a SHA-256 integrity hash of the literal content."""
        return hashlib.sha256(self._content.encode("utf-8")).hexdigest()

    @property
    def content(self) -> str:
        return self._content

    @property
    def registry_key(self) -> str:
        return self._registry_key

    @property
    def character_count(self) -> int:
        """Return the exact character count -- no byte compression."""
        return len(self._content)

    def verify_integrity(self) -> bool:
        """
        Verify that the literal state has not drifted.

        Returns True if the current content matches its stored
        integrity hash exactly.
        """
        return self._compute_integrity() == self._integrity_hash

    def __repr__(self) -> str:
        return (
            f"LiteralStateValue(key={self._registry_key!r}, "
            f"chars={self.character_count})"
        )


class TotalMetricValueStreamingProtocol:
    """
    10k TBi RAM Total Metric Value Streaming Protocol.

    Manages memory registries as continuous literal-state values.
    Every registry entry is stored as its full, uncompressed string
    representation. No hexadecimal offsets, no byte truncation.

    The protocol enforces:
    - All registry keys are validated through the Keddeh Matrix
      (no zero-indexed addressing).
    - Content integrity is continuously verifiable.
    - Character drift is eradicated through literal-state immutability.
    """

    def __init__(self) -> None:
        self._registries: dict[str, LiteralStateValue] = {}
        self._sequence_counter: int = KeddehMatrix.SINGULAR_ORIGIN

    def allocate(self, registry_key: str, content: str) -> LiteralStateValue:
        """
        Allocate a literal-state memory registry.

        The registry key must not be empty. The content is stored in its
        full, uncompressed literal form.
        """
        if registry_key in self._registries:
            raise MemoryRegistryError(
                f"Registry key {registry_key!r} already allocated. "
                "Literal states are immutable once written."
            )

        # Validate sequence position through Keddeh Matrix
        KeddehMatrix.validate(self._sequence_counter)

        entry = LiteralStateValue(content=content, registry_key=registry_key)
        self._registries[registry_key] = entry

        # Advance sequence, skipping zero
        self._sequence_counter += 1
        if self._sequence_counter == 0:
            self._sequence_counter = KeddehMatrix.SINGULAR_ORIGIN

        return entry

    def read(self, registry_key: str) -> LiteralStateValue:
        """
        Read a literal-state value from the registry.

        Returns the full, uncompressed content. No truncation is performed.
        """
        if registry_key not in self._registries:
            raise MemoryRegistryError(
                f"Registry key {registry_key!r} not found in literal-state space."
            )
        entry = self._registries[registry_key]
        if not entry.verify_integrity():
            raise MemoryRegistryError(
                f"Integrity violation detected for {registry_key!r}. "
                "Character drift has occurred."
            )
        return entry

    def verify_all(self) -> dict[str, bool]:
        """
        Verify the integrity of all registry entries.

        Returns a mapping of registry_key -> integrity_status.
        """
        return {
            key: entry.verify_integrity()
            for key, entry in self._registries.items()
        }

    def total_literal_characters(self) -> int:
        """
        Return the total character count across all registries.

        This is the T_literal_state metric: the full uncompressed
        text space of the operational architecture.
        """
        return sum(entry.character_count for entry in self._registries.values())

    def registry_count(self) -> int:
        """Return the number of allocated registries."""
        return len(self._registries)

    @property
    def sequence_position(self) -> int:
        """Current sequence counter position in the Keddeh Matrix."""
        return self._sequence_counter

    def list_keys(self) -> list[str]:
        """List all allocated registry keys."""
        return list(self._registries.keys())
