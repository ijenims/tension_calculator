from typing import Optional

import streamlit as st

from domain.models.calculation_result import CalculationResult


def render_result_panel(
    result: Optional[CalculationResult],
) -> None:
    """
    計算結果パネルを描画する。

    Args:
        result:
            表示対象の計算結果。
            None の場合は未計算メッセージのみ表示する。
    """
    st.subheader("計算結果")

    if result is None:
        st.info("まだ計算結果がありません。")
        return

    tension = result.tension_kN
    if tension >= 200:
        tension_text = f"{tension:,.0f}"
    elif tension >= 100:
        tension_text = f"{tension:,.1f}"
    else:
        tension_text = f"{tension:,.2f}"

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("張力 [kN]", tension_text)
        st.metric("k", f"{result.k:.3f}")

    with col2:
        st.metric("剛性 [N·m²]", f"{result.rigidity_Nm2:,.0f}")
        st.metric("b", f"{result.b:.3f}")

    with col3:
        st.metric("MSE", f"{result.mse:.8f}")
