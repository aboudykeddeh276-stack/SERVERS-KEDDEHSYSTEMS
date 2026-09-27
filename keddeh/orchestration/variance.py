from __future__ import annotations

import math
from typing import Any, Dict, List

from pydantic import BaseModel, Field


class OperationalMetrics(BaseModel):
    latency_ms: float = Field(..., ge=0.0)
    token_cost_input: int = Field(..., ge=0)
    token_cost_output: int = Field(..., ge=0)
    execution_success: int = Field(..., ge=0, le=1)


class StatisticalProfile(BaseModel):
    mean: float
    variance: float
    standard_deviation: float


class MetricVarianceEngine:
    @staticmethod
    def calculate_statistical_profile(data_pool: List[float]) -> StatisticalProfile:
        n = len(data_pool)
        if n < 2:
            return StatisticalProfile(
                mean=sum(data_pool) / max(n, 1),
                variance=0.0,
                standard_deviation=0.0,
            )

        mean_val = sum(data_pool) / n
        squared_deviations_sum = sum((x - mean_val) ** 2 for x in data_pool)
        variance_val = squared_deviations_sum / (n - 1)
        return StatisticalProfile(
            mean=mean_val,
            variance=variance_val,
            standard_deviation=math.sqrt(variance_val),
        )

    def evaluates_runtime_drift(
        self,
        baseline_pool: List[float],
        current_observation: float,
        threshold_sigmas: float = 3.0,
    ) -> Dict[str, Any]:
        if len(baseline_pool) < 5:
            return {"anomalous_drift_detected": False, "reason": "INSUFFICIENT_BASELINE_DATA"}

        profile = self.calculate_statistical_profile(baseline_pool)
        if profile.standard_deviation == 0:
            return {
                "anomalous_drift_detected": current_observation != profile.mean,
                "z_score": 0.0,
                "mean_baseline": profile.mean,
                "standard_deviation": profile.standard_deviation,
                "observation_variance": current_observation - profile.mean,
            }

        z_score = abs(current_observation - profile.mean) / profile.standard_deviation
        return {
            "anomalous_drift_detected": z_score > threshold_sigmas,
            "z_score": z_score,
            "mean_baseline": profile.mean,
            "standard_deviation": profile.standard_deviation,
            "observation_variance": current_observation - profile.mean,
        }


if __name__ == "__main__":
    engine = MetricVarianceEngine()
    print(engine.evaluates_runtime_drift([100, 101, 99, 102, 98, 100], 150))
