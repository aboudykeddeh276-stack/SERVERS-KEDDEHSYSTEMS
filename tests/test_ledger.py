"""Tests for the Singular Observer Booted-State Ledger."""

import pytest

from keddeh_matrix.kex_seed import KEXSeed
from keddeh_matrix.ledger import SingularObserverLedger, LedgerError


class TestSingularObserverLedger:
    """Test the booted-state ledger."""

    def setup_method(self):
        self.ledger = SingularObserverLedger()
        self.seed_a = KEXSeed(
            node_id="A", literal_state="state_A", matrix_position=1
        )
        self.seed_b = KEXSeed(
            node_id="B", literal_state="state_B", matrix_position=3
        )
        self.seed_c = KEXSeed(
            node_id="C", literal_state="state_C", matrix_position=-2
        )

    def test_register_nodes(self):
        self.ledger.register_node(self.seed_a)
        self.ledger.register_node(self.seed_b)
        assert self.ledger.node_count == 2

    def test_duplicate_registration_rejected(self):
        self.ledger.register_node(self.seed_a)
        with pytest.raises(LedgerError, match="already registered"):
            self.ledger.register_node(self.seed_a)

    def test_not_booted_initially(self):
        assert self.ledger.is_booted is False

    def test_boot_resolves_routes(self):
        self.ledger.register_node(self.seed_a)
        self.ledger.register_node(self.seed_b)
        self.ledger.register_node(self.seed_c)
        count = self.ledger.boot()
        assert count == 6  # 3 nodes, 3*2 = 6 directional routes
        assert self.ledger.is_booted is True

    def test_lookup_after_boot(self):
        self.ledger.register_node(self.seed_a)
        self.ledger.register_node(self.seed_b)
        self.ledger.boot()
        entry = self.ledger.lookup("A", "B")
        assert entry.source_node_id == "A"
        assert entry.target_node_id == "B"
        assert entry.measured_perspective == 2  # 3 - 1

    def test_lookup_before_boot_fails(self):
        self.ledger.register_node(self.seed_a)
        with pytest.raises(LedgerError, match="not booted"):
            self.ledger.lookup("A", "B")

    def test_mirror_crossing_in_entry(self):
        self.ledger.register_node(self.seed_a)
        self.ledger.register_node(self.seed_c)
        self.ledger.boot()
        entry = self.ledger.lookup("A", "C")
        assert entry.mirror_crossing is True
        assert entry.routing_mode == "instantaneous_boundary_crossing"

    def test_new_node_invalidates_boot(self):
        self.ledger.register_node(self.seed_a)
        self.ledger.register_node(self.seed_b)
        self.ledger.boot()
        assert self.ledger.is_booted is True
        self.ledger.register_node(self.seed_c)
        assert self.ledger.is_booted is False
