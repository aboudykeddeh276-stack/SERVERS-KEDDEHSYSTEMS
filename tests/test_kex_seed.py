"""Tests for KEX Seeds and Discrepancy Vector Records."""

import pytest

from keddeh_matrix.core import KeddehMatrixError
from keddeh_matrix.kex_seed import (
    KEXSeed,
    KEXSeedError,
    DiscrepancyVector,
    AbsoluteMathematicalStateSeedAndDiscrepancyVectorRecord,
)


class TestKEXSeed:
    """Test KEX seed creation and properties."""

    def test_create_valid_seed(self):
        seed = KEXSeed(node_id="node_A", literal_state="state_A", matrix_position=1)
        assert seed.node_id == "node_A"
        assert seed.matrix_position == 1

    def test_reject_zero_position(self):
        with pytest.raises(KeddehMatrixError):
            KEXSeed(node_id="node_A", literal_state="state", matrix_position=0)

    def test_reject_empty_node_id(self):
        with pytest.raises(KEXSeedError):
            KEXSeed(node_id="", literal_state="state", matrix_position=1)

    def test_fingerprint_is_deterministic(self):
        seed1 = KEXSeed(node_id="n", literal_state="s", matrix_position=2)
        seed2 = KEXSeed(node_id="n", literal_state="s", matrix_position=2)
        assert seed1.fingerprint == seed2.fingerprint

    def test_character_count(self):
        seed = KEXSeed(node_id="n", literal_state="abcdef", matrix_position=1)
        assert seed.character_count == 6


class TestDiscrepancyVector:
    """Test structural drift computation."""

    def test_identical_states_zero_drift(self):
        dv = DiscrepancyVector(target_state="hello", baseline_state="hello")
        assert dv.mismatch_count == 0
        assert dv.drift_factor == 0.0
        assert dv.is_resolved is True

    def test_completely_different_states(self):
        dv = DiscrepancyVector(target_state="abc", baseline_state="xyz")
        assert dv.mismatch_count == 3
        assert dv.drift_factor == 1.0

    def test_partial_mismatch(self):
        dv = DiscrepancyVector(target_state="hello", baseline_state="hxllo")
        assert dv.mismatch_count == 1
        assert dv.mismatch_positions == [1]

    def test_length_difference_counted_as_drift(self):
        dv = DiscrepancyVector(target_state="hi", baseline_state="hello")
        # positions 2, 3, 4 are mismatches (beyond shorter string)
        assert dv.mismatch_count >= 3

    def test_empty_states(self):
        dv = DiscrepancyVector(target_state="", baseline_state="")
        assert dv.is_resolved is True
        assert dv.drift_factor == 0.0


class TestAbsoluteMathematicalStateSeedAndDiscrepancyVectorRecord:
    """Test the KEX seed record and resolution process."""

    def test_register_and_retrieve_seed(self):
        record = AbsoluteMathematicalStateSeedAndDiscrepancyVectorRecord()
        seed = KEXSeed(node_id="n1", literal_state="state", matrix_position=1)
        record.register_seed(seed)
        assert record.get_seed("n1") == seed

    def test_duplicate_registration_rejected(self):
        record = AbsoluteMathematicalStateSeedAndDiscrepancyVectorRecord()
        seed = KEXSeed(node_id="n1", literal_state="s", matrix_position=1)
        record.register_seed(seed)
        with pytest.raises(KEXSeedError, match="already registered"):
            record.register_seed(seed)

    def test_resolution_drives_drift_to_zero(self):
        record = AbsoluteMathematicalStateSeedAndDiscrepancyVectorRecord()
        corrected = record.execute_resolution_process(
            target_state="hxllo wxrld",
            baseline_state="hello world",
        )
        assert corrected == "hello world"

    def test_resolution_handles_length_difference(self):
        record = AbsoluteMathematicalStateSeedAndDiscrepancyVectorRecord()
        corrected = record.execute_resolution_process(
            target_state="hi",
            baseline_state="hello",
        )
        assert corrected == "hello"

    def test_resolution_log_populated(self):
        record = AbsoluteMathematicalStateSeedAndDiscrepancyVectorRecord()
        record.execute_resolution_process(
            target_state="abc",
            baseline_state="xyz",
        )
        assert len(record.resolution_log) > 0

    def test_already_resolved_state(self):
        record = AbsoluteMathematicalStateSeedAndDiscrepancyVectorRecord()
        corrected = record.execute_resolution_process(
            target_state="perfect",
            baseline_state="perfect",
        )
        assert corrected == "perfect"
        log = record.resolution_log
        assert any(entry["status"] == "resolved" for entry in log)
