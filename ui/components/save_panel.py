from typing import Optional

import streamlit as st

from domain.models.calculation_result import CalculationResult


def render_save_panel(
    save_enabled: bool,
    result: Optional[CalculationResult],
) -> bool:
    """
    保存パネルを描画し、保存ボタン押下状態を返す。

    Args:
        save_enabled:
            「結果保存」チェック状態。
        result:
            現在の計算結果。None の場合は保存不可。

    Returns:
        bool:
            保存ボタンが押された場合 True。
    """
    st.subheader("保存")

    if not save_enabled:
        st.caption("サイドバーで「結果保存」をONにすると保存できます。")
        return False

    if result is None:
        st.warning("保存対象の計算結果がありません。")
        return False

    return st.button(
        label="結果を保存",
        use_container_width=True,
        key="save_panel_execute_save",
    )