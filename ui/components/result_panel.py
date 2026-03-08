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

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("張力 [kN]", f"{result.tension_kN:.3f}")
        st.metric("k", f"{result.k:.5f}")

    with col2:
        st.metric("剛性 [N·m²]", f"{result.rigidity_Nm2:.3f}")
        st.metric("b", f"{result.b:.5f}")

    with col3:
        st.metric("MSE", f"{result.mse:.8f}")
        if result.xi is not None:
            st.metric("ξ", f"{result.xi:.5f}")
        else:
            st.metric("ξ", "-")