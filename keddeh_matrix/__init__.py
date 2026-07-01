"""
Keddeh Matrix Hyper-Explicit Mesh Operating System

Core implementation of the zero-less Keddeh Matrix (-3 | -2 | 1 | +2 | +3)
and its derived protocols for memory addressing, network emulation, and
mesh routing.

Deployed by Keddeh Systems.
"""

from keddeh_matrix.core import KeddehMatrix
from keddeh_matrix.streaming_protocol import TotalMetricValueStreamingProtocol
from keddeh_matrix.kex_seed import (
    AbsoluteMathematicalStateSeedAndDiscrepancyVectorRecord,
)
from keddeh_matrix.mesh_routing import FormulaOfPerspectiveRouter
from keddeh_matrix.ledger import SingularObserverLedger
from keddeh_matrix.agents import (
    BrainKLevelSixNeuroEmulationAndMathematicalLimitEvaluationAgent,
)

__all__ = [
    "KeddehMatrix",
    "TotalMetricValueStreamingProtocol",
    "AbsoluteMathematicalStateSeedAndDiscrepancyVectorRecord",
    "FormulaOfPerspectiveRouter",
    "SingularObserverLedger",
    "BrainKLevelSixNeuroEmulationAndMathematicalLimitEvaluationAgent",
]
