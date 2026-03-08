from dataclasses import dataclass
from typing import Optional


@dataclass
class CableRecord:

    facility_name: str
    cable_no: str
    branch_no: str

    unit_weight_kg_per_m: float
    cable_length_m: float

    design_tension_kN: float
    design_rigidity_Nm2: Optional[float]

    xi: Optional[float]

    measured_frequencies_hz: list[Optional[float]]
    max_mode: int = 7

    calculated_tension_kN: Optional[float] = None
    calculated_rigidity_Nm2: Optional[float] = None
    beta: Optional[float] = None