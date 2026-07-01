"""
Keddeh Matrix Core

Defines the zero-less Keddeh Matrix number line: (-3 | -2 | 1 | +2 | +3).

The Keddeh Matrix explicitly eliminates the Cartesian absolute zero origin (0,0).
Instead of treating zero as a valid numeric state, the matrix operates on the
principle that every computational value must be a defined structural state --
a "1 whole". The number line skips zero entirely, using 1 as the singular
positive origin and mirroring symmetrically into the negative domain.

Matrix Definition:
    ... -3 | -2 | -1 | +1 | +2 | +3 ...
    (Zero is structurally excluded.)

The five reference points (-3 | -2 | 1 | +2 | +3) define the calibration
boundaries of the matrix, where 1 is the Singular Origin.
"""

from __future__ import annotations

from typing import Union

Number = Union[int, float]


class KeddehMatrixError(Exception):
    """Raised when a zero-state violation occurs in the Keddeh Matrix."""


class KeddehMatrix:
    """
    The zero-less Keddeh Matrix.

    Provides arithmetic and validation operations that enforce the structural
    exclusion of zero. Every value passing through the matrix is guaranteed
    to be a defined, non-zero relational state.

    The five calibration anchors are: -3, -2, +1, +2, +3.
    The Singular Origin is +1.
    """

    SINGULAR_ORIGIN: int = 1
    CALIBRATION_ANCHORS: tuple[int, ...] = (-3, -2, -1, 1, 2, 3)
    NEGATIVE_BOUNDARY: int = -3
    POSITIVE_BOUNDARY: int = 3

    @staticmethod
    def validate(value: Number) -> Number:
        """
        Validate that a value is a legal Keddeh Matrix state.

        Raises KeddehMatrixError if the value is zero, as zero represents
        a structurally undefined state in the matrix.
        """
        if value == 0:
            raise KeddehMatrixError(
                "Zero is structurally excluded from the Keddeh Matrix. "
                "All values must be defined relational states."
            )
        return value

    @classmethod
    def project(cls, value: Number) -> Number:
        """
        Project a standard numeric value into the Keddeh Matrix.

        Values of zero are mapped to the Singular Origin (+1).
        All other values pass through validated.
        """
        if value == 0:
            return cls.SINGULAR_ORIGIN
        return value

    @classmethod
    def add(cls, a: Number, b: Number) -> Number:
        """
        Keddeh Matrix addition.

        If the standard sum would be zero, the result is projected
        to the Singular Origin to maintain structural continuity.
        """
        cls.validate(a)
        cls.validate(b)
        result = a + b
        return cls.project(result)

    @classmethod
    def subtract(cls, a: Number, b: Number) -> Number:
        """
        Keddeh Matrix subtraction.

        If the standard difference would be zero, the result is projected
        to the Singular Origin.
        """
        cls.validate(a)
        cls.validate(b)
        result = a - b
        return cls.project(result)

    @classmethod
    def multiply(cls, a: Number, b: Number) -> Number:
        """
        Keddeh Matrix multiplication.

        Standard multiplication between non-zero values can never produce
        zero, so the result is returned directly after validation.
        """
        cls.validate(a)
        cls.validate(b)
        result = a * b
        return cls.project(result)

    @classmethod
    def mirror(cls, value: Number) -> Number:
        """
        Mirror a value across the Keddeh Matrix boundary.

        Reflects a value symmetrically: positive becomes negative and
        vice versa. The matrix boundary crossing is instantaneous --
        there is no traversal through a zero gap.

        mirror(+2) -> -2
        mirror(-3) -> +3
        mirror(+1) -> -1
        """
        cls.validate(value)
        return -value

    @classmethod
    def calibration_position(cls, value: Number) -> int:
        """
        Return the nearest calibration anchor index for a given value.

        Maps any valid Keddeh Matrix value to its nearest structural
        anchor in the calibration set (-3, -2, -1, 1, 2, 3).
        """
        cls.validate(value)
        closest = min(cls.CALIBRATION_ANCHORS, key=lambda a: abs(a - value))
        return closest

    @classmethod
    def is_positive_domain(cls, value: Number) -> bool:
        """Check if a value resides in the positive domain (>= Singular Origin)."""
        cls.validate(value)
        return value >= cls.SINGULAR_ORIGIN

    @classmethod
    def is_negative_domain(cls, value: Number) -> bool:
        """Check if a value resides in the negative domain (< 0, excluding zero)."""
        cls.validate(value)
        return value < 0

    @classmethod
    def boundary_distance(cls, value: Number) -> Number:
        """
        Calculate the structural distance of a value from the matrix
        mirror boundary (the gap where zero would exist).

        For positive values, this is the value itself.
        For negative values, this is the absolute value.
        The minimum possible distance is 1 (the Singular Origin).
        """
        cls.validate(value)
        return abs(value)
