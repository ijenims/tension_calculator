import streamlit as st
import pandas as pd
from typing import Optional

from domain.models.cable_record import CableRecord


def _fmt(value: Optional[float], digits: int = 3) -> str:
    if value is None:
        return "-"
    return f"{value:.{digits}f}"


def render_spec_panel(cable: Optional[CableRecord]) -> None:
    """
    ケーブル諸元表示（横並び）
    """
    if cable is None:
        return

    st.caption("ケーブル諸元")

    df = pd.DataFrame(
        [{
            "単位重量 [kg/m]": _fmt(cable.unit_weight_kg_per_m, 3),
            "ケーブル長 [m]": _fmt(cable.cable_length_m, 3),
            "設計張力 [kN]": _fmt(cable.design_tension_kN, 3),
            "設計剛性 [Nm²]": _fmt(cable.design_rigidity_Nm2, 0),
            "ξ": _fmt(cable.xi, 4),
        }]
    )

    st.dataframe(df, use_container_width=True, hide_index=True)
