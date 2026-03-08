from dataclasses import dataclass
from typing import Optional


@dataclass
class CalculationResult:
    k: float
    b: float

    tension_kN: float
    rigidity_Nm2: float

    xi: Optional[float]
    mse: float

    measured_frequencies_hz: list[Optional[float]]
    theoretical_frequencies_hz: list[float]

    use_mask: list[bool]
    max_mode: int