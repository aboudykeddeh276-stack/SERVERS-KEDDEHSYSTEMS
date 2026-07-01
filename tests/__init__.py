"""Tests for the Keddeh Matrix core."""

import pytest

from keddeh_matrix.core import KeddehMatrix, KeddehMatrixError


class TestKeddehMatrixValidation:
    """Test zero exclusion and validation."""

    def test_validate_rejects_zero(self):
        with pytest.raises(KeddehMatrixError, match="structurally excluded"):
            KeddehMatrix.validate(0)

    def test_validate_rejects_zero_float(self):
        with pytest.raises(KeddehMatrixError):
            KeddehMatrix.validate(0.0)

    def test_validate_accepts_positive(self):
        assert KeddehMatrix.validate(1) == 1
        assert KeddehMatrix.validate(42) == 42

    def test_validate_accepts_negative(self):
        assert KeddehMatrix.validate(-1) == -1
        assert KeddehMatrix.validate(-3) == -3

    def test_validate_accepts_floats(self):
        assert KeddehMatrix.validate(0.5) == 0.5
        assert KeddehMatrix.validate(-2.7) == -2.7


class TestKeddehMatrixProject:
    """Test projection into the matrix."""

    def test_project_zero_maps_to_singular_origin(self):
        assert KeddehMatrix.project(0) == 1

    def test_project_nonzero_passes_through(self):
        assert KeddehMatrix.project(5) == 5
        assert KeddehMatrix.project(-3) == -3


class TestKeddehMatrixArithmetic:
    """Test matrix arithmetic operations."""

    def test_add_normal(self):
        assert KeddehMatrix.add(2, 3) == 5

    def test_add_would_produce_zero_projects_to_origin(self):
        # 3 + (-3) = 0 -> projected to 1
        assert KeddehMatrix.add(3, -3) == 1

    def test_add_rejects_zero_input(self):
        with pytest.raises(KeddehMatrixError):
            KeddehMatrix.add(0, 5)

    def test_subtract_normal(self):
        assert KeddehMatrix.subtract(5, 2) == 3

    def test_subtract_would_produce_zero_projects_to_origin(self):
        # 3 - 3 = 0 -> projected to 1
        assert KeddehMatrix.subtract(3, 3) == 1

    def test_multiply_normal(self):
        assert KeddehMatrix.multiply(3, 4) == 12

    def test_multiply_negative(self):
        assert KeddehMatrix.multiply(-2, 3) == -6


class TestKeddehMatrixMirror:
    """Test mirror boundary crossing."""

    def test_mirror_positive_to_negative(self):
        assert KeddehMatrix.mirror(2) == -2

    def test_mirror_negative_to_positive(self):
        assert KeddehMatrix.mirror(-3) == 3

    def test_mirror_singular_origin(self):
        assert KeddehMatrix.mirror(1) == -1

    def test_mirror_rejects_zero(self):
        with pytest.raises(KeddehMatrixError):
            KeddehMatrix.mirror(0)

    def test_double_mirror_is_identity(self):
        assert KeddehMatrix.mirror(KeddehMatrix.mirror(7)) == 7


class TestKeddehMatrixCalibration:
    """Test calibration anchor mapping."""

    def test_calibration_exact_anchor(self):
        assert KeddehMatrix.calibration_position(2) == 2
        assert KeddehMatrix.calibration_position(-3) == -3

    def test_calibration_between_anchors(self):
        # 4 is closest to 3
        assert KeddehMatrix.calibration_position(4) == 3

    def test_calibration_large_negative(self):
        assert KeddehMatrix.calibration_position(-100) == -3


class TestKeddehMatrixDomains:
    """Test domain classification."""

    def test_positive_domain(self):
        assert KeddehMatrix.is_positive_domain(1) is True
        assert KeddehMatrix.is_positive_domain(5) is True

    def test_negative_domain(self):
        assert KeddehMatrix.is_negative_domain(-1) is True
        assert KeddehMatrix.is_negative_domain(-3) is True

    def test_boundary_distance(self):
        assert KeddehMatrix.boundary_distance(3) == 3
        assert KeddehMatrix.boundary_distance(-2) == 2
        assert KeddehMatrix.boundary_distance(1) == 1
