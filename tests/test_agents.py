"""Tests for the BrainK Level 6 Agent."""

import pytest

from keddeh_matrix.agents import (
    BrainKLevelSixNeuroEmulationAndMathematicalLimitEvaluationAgent,
)
from keddeh_matrix.ledger import LedgerError


class TestBrainKLevelSixAgent:
    """Test the orchestrating agent."""

    def setup_method(self):
        self.agent = (
            BrainKLevelSixNeuroEmulationAndMathematicalLimitEvaluationAgent()
        )

    def test_allocate_memory_registry(self):
        self.agent.allocate_memory_registry("reg_1", "literal content")
        status = self.agent.get_status()
        assert status.memory_registries_allocated == 1
        assert status.total_literal_characters == 15

    def test_deploy_kex_seed(self):
        seed = self.agent.deploy_kex_seed("node_A", "state_A", 1)
        assert seed.node_id == "node_A"
        status = self.agent.get_status()
        assert status.kex_seeds_registered == 1

    def test_resolve_structural_drift(self):
        corrected = self.agent.resolve_structural_drift(
            target_state="hxllo", baseline_state="hello"
        )
        assert corrected == "hello"
        status = self.agent.get_status()
        assert status.drift_resolutions_executed == 1

    def test_boot_ledger_and_route_lookup(self):
        self.agent.deploy_kex_seed("A", "state_A", 1)
        self.agent.deploy_kex_seed("B", "state_B", 3)
        self.agent.deploy_kex_seed("C", "state_C", -2)
        count = self.agent.boot_ledger()
        assert count == 6

        route = self.agent.route_lookup("A", "B")
        assert route["measured_perspective"] == 2
        assert route["mirror_crossing"] is False

        route = self.agent.route_lookup("A", "C")
        assert route["measured_perspective"] == -3
        assert route["mirror_crossing"] is True

    def test_verify_memory_integrity(self):
        self.agent.allocate_memory_registry("x", "data")
        result = self.agent.verify_memory_integrity()
        assert result == {"x": True}

    def test_full_workflow(self):
        """End-to-end: allocate memory, deploy seeds, resolve drift, boot, route."""
        # 1. Allocate memory registries
        self.agent.allocate_memory_registry("config", "server_config_data")
        self.agent.allocate_memory_registry("state", "operational_state_record")

        # 2. Deploy KEX seeds
        self.agent.deploy_kex_seed("rack_1", "rack_one_state", 1)
        self.agent.deploy_kex_seed("rack_2", "rack_two_state", 2)
        self.agent.deploy_kex_seed("rack_3", "rack_three_state", -1)

        # 3. Resolve structural drift
        corrected = self.agent.resolve_structural_drift(
            "rxck_one_stxte", "rack_one_state"
        )
        assert corrected == "rack_one_state"

        # 4. Boot ledger
        routes = self.agent.boot_ledger()
        assert routes == 6

        # 5. Route lookups
        route = self.agent.route_lookup("rack_1", "rack_3")
        assert route["mirror_crossing"] is True

        # 6. Verify final status
        status = self.agent.get_status()
        assert status.memory_registries_allocated == 2
        assert status.kex_seeds_registered == 3
        assert status.ledger_booted is True
        assert status.ledger_routes_resolved == 6
        assert status.drift_resolutions_executed == 1
