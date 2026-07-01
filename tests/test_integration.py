"""
Integration tests for the Keddeh Matrix Framework Validation Workflow.

Tests all workflow scripts for correct output structure, data integrity,
and cross-script integration. Provides coverage reporting.
"""

import json
import os
import sys
import tempfile
from pathlib import Path

import pytest

# Add scripts directory to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from keddeh_matrix_workflow import (
    KeddehMatrix,
    script_init_keddeh_framework,
    script_validate_arithmetic_operations,
    script_test_physical_calibration,
    script_compare_cartesian_vs_keddeh,
    script_generate_mathematical_proofs,
    script_integration_virtualised_memory,
    script_comprehensive_test_suite,
    script_generate_visualization,
    script_full_workflow,
)


@pytest.fixture
def output_dir(tmp_path):
    """Provide a temporary output directory for test artifacts."""
    return str(tmp_path / "reports")


# ============================================================================
# Unit Tests: KeddehMatrix dataclass
# ============================================================================

class TestKeddehMatrix:
    def test_default_creation(self):
        m = KeddehMatrix(value=5.0)
        assert m.value == 5.0
        assert m.is_boundary_observer is False

    def test_boundary_observer(self):
        m = KeddehMatrix(value=0.0, is_boundary_observer=True)
        assert m.is_boundary_observer is True

    def test_repr(self):
        m = KeddehMatrix(value=3.0, is_boundary_observer=True)
        assert "3.0" in repr(m)
        assert "observer=True" in repr(m)

    def test_negative_value(self):
        m = KeddehMatrix(value=-2.0)
        assert m.value == -2.0


# ============================================================================
# Integration Tests: Framework Initialization
# ============================================================================

class TestFrameworkInit:
    def test_returns_dict(self, output_dir):
        result = script_init_keddeh_framework(output_dir)
        assert isinstance(result, dict)

    def test_framework_name(self, output_dir):
        result = script_init_keddeh_framework(output_dir)
        assert result["name"] == "1-Keddeh Matrix Framework"

    def test_version_present(self, output_dir):
        result = script_init_keddeh_framework(output_dir)
        assert result["version"] == "1.0.0"

    def test_core_axioms_count(self, output_dir):
        result = script_init_keddeh_framework(output_dir)
        assert len(result["core_axioms"]) == 5

    def test_key_sequence_no_zero(self, output_dir):
        result = script_init_keddeh_framework(output_dir)
        seq = result["key_sequence"]
        all_numbers = seq["before_boundary"] + seq["after_boundary"]
        assert 0 not in all_numbers

    def test_output_file_created(self, output_dir):
        script_init_keddeh_framework(output_dir)
        output_file = Path(output_dir) / "keddeh_framework_init.json"
        assert output_file.exists()

    def test_output_file_valid_json(self, output_dir):
        script_init_keddeh_framework(output_dir)
        output_file = Path(output_dir) / "keddeh_framework_init.json"
        data = json.loads(output_file.read_text())
        assert data["name"] == "1-Keddeh Matrix Framework"


# ============================================================================
# Integration Tests: Arithmetic Validation
# ============================================================================

class TestArithmeticValidation:
    def test_returns_dict(self, output_dir):
        result = script_validate_arithmetic_operations(output_dir)
        assert isinstance(result, dict)

    def test_validation_complete(self, output_dir):
        result = script_validate_arithmetic_operations(output_dir)
        assert result["status"] == "VALIDATION_COMPLETE"

    def test_all_operations_present(self, output_dir):
        result = script_validate_arithmetic_operations(output_dir)
        ops = result["operations"]
        assert "addition" in ops
        assert "subtraction" in ops
        assert "multiplication" in ops
        assert "division" in ops

    def test_all_test_cases_pass(self, output_dir):
        result = script_validate_arithmetic_operations(output_dir)
        for op_name, op_data in result["operations"].items():
            for tc in op_data["test_cases"]:
                assert tc["passes"], f"{op_name}: {tc}"

    def test_addition_correctness(self, output_dir):
        result = script_validate_arithmetic_operations(output_dir)
        cases = result["operations"]["addition"]["test_cases"]
        for tc in cases:
            assert tc["actual"] == tc["expected"]

    def test_division_correctness(self, output_dir):
        result = script_validate_arithmetic_operations(output_dir)
        cases = result["operations"]["division"]["test_cases"]
        for tc in cases:
            assert tc["actual"] == tc["expected"]

    def test_output_file_created(self, output_dir):
        script_validate_arithmetic_operations(output_dir)
        output_file = Path(output_dir) / "keddeh_arithmetic_validation.json"
        assert output_file.exists()


# ============================================================================
# Integration Tests: Physical Calibration
# ============================================================================

class TestPhysicalCalibration:
    def test_returns_dict(self, output_dir):
        result = script_test_physical_calibration(output_dir)
        assert isinstance(result, dict)

    def test_overall_pass(self, output_dir):
        result = script_test_physical_calibration(output_dir)
        assert result["overall_status"] == "ALL_SCENARIOS_PASS"

    def test_all_systems_validated(self, output_dir):
        result = script_test_physical_calibration(output_dir)
        systems = result["systems"]
        assert "temperature" in systems
        assert "voltage" in systems
        assert "motion" in systems

    def test_each_system_validated(self, output_dir):
        result = script_test_physical_calibration(output_dir)
        for name, system in result["systems"].items():
            assert system["status"] == "VALIDATED", f"{name} not validated"

    def test_all_scenarios_pass(self, output_dir):
        result = script_test_physical_calibration(output_dir)
        for name, system in result["systems"].items():
            for scenario in system["test_scenarios"]:
                assert scenario["passes"], f"{name}: scenario failed"

    def test_output_file_created(self, output_dir):
        script_test_physical_calibration(output_dir)
        output_file = Path(output_dir) / "keddeh_physical_calibration.json"
        assert output_file.exists()


# ============================================================================
# Integration Tests: Cartesian vs Keddeh Comparison
# ============================================================================

class TestCartesianComparison:
    def test_returns_dict(self, output_dir):
        result = script_compare_cartesian_vs_keddeh(output_dir)
        assert isinstance(result, dict)

    def test_three_problems_analyzed(self, output_dir):
        result = script_compare_cartesian_vs_keddeh(output_dir)
        assert "problem_1_dimensional_collapse" in result
        assert "problem_2_division_by_zero" in result
        assert "problem_3_zero_gap_discontinuity" in result

    def test_keddeh_resolves_problems(self, output_dir):
        result = script_compare_cartesian_vs_keddeh(output_dir)
        assert result["problem_1_dimensional_collapse"]["keddeh_solution"]["status"] == "RESOLVED"
        assert result["problem_3_zero_gap_discontinuity"]["keddeh_solution"]["status"] == "RESOLVED"

    def test_strengths_comparison_present(self, output_dir):
        result = script_compare_cartesian_vs_keddeh(output_dir)
        assert len(result["strengths_comparison"]["cartesian_strengths"]) > 0
        assert len(result["strengths_comparison"]["keddeh_strengths"]) > 0

    def test_output_file_created(self, output_dir):
        script_compare_cartesian_vs_keddeh(output_dir)
        output_file = Path(output_dir) / "keddeh_cartesian_comparison.json"
        assert output_file.exists()


# ============================================================================
# Integration Tests: Mathematical Proofs
# ============================================================================

class TestMathematicalProofs:
    def test_returns_dict(self, output_dir):
        result = script_generate_mathematical_proofs(output_dir)
        assert isinstance(result, dict)

    def test_proofs_generated(self, output_dir):
        result = script_generate_mathematical_proofs(output_dir)
        assert result["status"] == "PROOFS_GENERATED"

    def test_four_theorems(self, output_dir):
        result = script_generate_mathematical_proofs(output_dir)
        assert len(result["theorems"]) == 4

    def test_proven_theorems(self, output_dir):
        result = script_generate_mathematical_proofs(output_dir)
        proven = [t for t, v in result["theorems"].items() if v["status"] == "PROVEN"]
        assert len(proven) >= 3

    def test_output_file_created(self, output_dir):
        script_generate_mathematical_proofs(output_dir)
        output_file = Path(output_dir) / "keddeh_mathematical_proofs.json"
        assert output_file.exists()


# ============================================================================
# Integration Tests: VIRTUALISED_MEMORY Integration
# ============================================================================

class TestVirtualisedMemoryIntegration:
    def test_returns_dict(self, output_dir):
        result = script_integration_virtualised_memory(output_dir)
        assert isinstance(result, dict)

    def test_perfect_alignment(self, output_dir):
        result = script_integration_virtualised_memory(output_dir)
        assert result["keddeh_compatibility"]["alignment"] == "PERFECT"

    def test_no_zero_axis(self, output_dir):
        result = script_integration_virtualised_memory(output_dir)
        assert result["virtualised_memory_properties"]["no_zero_axis"] is True

    def test_indexing_starts_at_1(self, output_dir):
        result = script_integration_virtualised_memory(output_dir)
        assert result["virtualised_memory_properties"]["indexing_start"] == 1

    def test_all_test_cases_pass(self, output_dir):
        result = script_integration_virtualised_memory(output_dir)
        for name, tc in result["test_cases"].items():
            assert tc["passes"], f"{name} failed"

    def test_production_ready(self, output_dir):
        result = script_integration_virtualised_memory(output_dir)
        assert result["production_readiness"]["status"] == "READY"

    def test_output_file_created(self, output_dir):
        script_integration_virtualised_memory(output_dir)
        output_file = Path(output_dir) / "keddeh_virtualised_memory_integration.json"
        assert output_file.exists()


# ============================================================================
# Integration Tests: Comprehensive Test Suite
# ============================================================================

class TestComprehensiveTestSuite:
    def test_returns_dict(self, output_dir):
        result = script_comprehensive_test_suite(output_dir)
        assert isinstance(result, dict)

    def test_all_tests_pass(self, output_dir):
        result = script_comprehensive_test_suite(output_dir)
        assert result["status"] == "ALL_TESTS_PASSED"

    def test_no_failures(self, output_dir):
        result = script_comprehensive_test_suite(output_dir)
        assert result["failed"] == 0

    def test_total_count_correct(self, output_dir):
        result = script_comprehensive_test_suite(output_dir)
        assert result["total_tests"] == result["passed"] + result["failed"]

    def test_three_categories(self, output_dir):
        result = script_comprehensive_test_suite(output_dir)
        assert len(result["test_categories"]) == 3

    def test_integration_category_present(self, output_dir):
        result = script_comprehensive_test_suite(output_dir)
        assert "integration" in result["test_categories"]

    def test_output_file_created(self, output_dir):
        script_comprehensive_test_suite(output_dir)
        output_file = Path(output_dir) / "keddeh_comprehensive_test_suite.json"
        assert output_file.exists()


# ============================================================================
# Integration Tests: Visualization
# ============================================================================

class TestVisualization:
    def test_returns_dict(self, output_dir):
        result = script_generate_visualization(output_dir)
        assert isinstance(result, dict)

    def test_status_generated(self, output_dir):
        result = script_generate_visualization(output_dir)
        assert result["status"] == "GENERATED"

    def test_number_line_comparison(self, output_dir):
        result = script_generate_visualization(output_dir)
        assert "cartesian" in result["number_line_comparison"]
        assert "keddeh" in result["number_line_comparison"]

    def test_keddeh_uses_observer_boundary(self, output_dir):
        result = script_generate_visualization(output_dir)
        assert "OBSERVER_BOUNDARY" in result["number_line_comparison"]["keddeh"]

    def test_output_file_created(self, output_dir):
        script_generate_visualization(output_dir)
        output_file = Path(output_dir) / "keddeh_visualization_metadata.json"
        assert output_file.exists()


# ============================================================================
# End-to-End Integration Test: Full Workflow
# ============================================================================

class TestFullWorkflow:
    def test_returns_dict(self, output_dir):
        result = script_full_workflow(output_dir)
        assert isinstance(result, dict)

    def test_workflow_completed(self, output_dir):
        result = script_full_workflow(output_dir)
        assert result["status"] == "COMPLETED"

    def test_all_scripts_succeed(self, output_dir):
        result = script_full_workflow(output_dir)
        assert result["summary"]["failed"] == 0

    def test_eight_scripts_executed(self, output_dir):
        result = script_full_workflow(output_dir)
        assert result["summary"]["total_scripts"] == 8
        assert result["summary"]["successful"] == 8

    def test_all_output_files_created(self, output_dir):
        script_full_workflow(output_dir)
        expected_files = [
            "keddeh_framework_init.json",
            "keddeh_arithmetic_validation.json",
            "keddeh_physical_calibration.json",
            "keddeh_cartesian_comparison.json",
            "keddeh_mathematical_proofs.json",
            "keddeh_virtualised_memory_integration.json",
            "keddeh_comprehensive_test_suite.json",
            "keddeh_visualization_metadata.json",
            "keddeh_workflow_complete.json",
        ]
        output_path = Path(output_dir)
        for fname in expected_files:
            assert (output_path / fname).exists(), f"Missing: {fname}"

    def test_all_output_files_valid_json(self, output_dir):
        script_full_workflow(output_dir)
        output_path = Path(output_dir)
        for f in output_path.glob("*.json"):
            data = json.loads(f.read_text())
            assert isinstance(data, dict), f"Invalid JSON in {f.name}"


# ============================================================================
# Cross-Script Integration Tests
# ============================================================================

class TestCrossScriptIntegration:
    """Tests that verify consistency across multiple workflow scripts."""

    def test_arithmetic_matches_comprehensive_suite(self, output_dir):
        arith = script_validate_arithmetic_operations(output_dir)
        suite = script_comprehensive_test_suite(output_dir)
        # Both should pass
        assert arith["status"] == "VALIDATION_COMPLETE"
        assert suite["status"] == "ALL_TESTS_PASSED"

    def test_integration_alignment_matches_comprehensive(self, output_dir):
        integration = script_integration_virtualised_memory(output_dir)
        suite = script_comprehensive_test_suite(output_dir)
        assert integration["keddeh_compatibility"]["alignment"] == "PERFECT"
        assert suite["test_categories"]["integration"]["passed"] == suite["test_categories"]["integration"]["total"]

    def test_framework_axioms_match_proofs(self, output_dir):
        framework = script_init_keddeh_framework(output_dir)
        proofs = script_generate_mathematical_proofs(output_dir)
        # Framework has 5 axioms, proofs has 4 theorems - theorems derive from axioms
        assert len(framework["core_axioms"]) >= len(proofs["theorems"])

    def test_no_zero_in_key_sequence_consistent(self, output_dir):
        framework = script_init_keddeh_framework(output_dir)
        integration = script_integration_virtualised_memory(output_dir)
        # Framework has no zero in key sequence
        all_nums = framework["key_sequence"]["before_boundary"] + framework["key_sequence"]["after_boundary"]
        assert 0 not in all_nums
        # Integration confirms no zero axis
        assert integration["virtualised_memory_properties"]["no_zero_axis"] is True
