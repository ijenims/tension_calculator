from dataclasses import dataclass
from typing import Optional

import streamlit as st

from config.defaults import (
    DEFAULT_B_MAX,
    DEFAULT_B_MIN,
    DEFAULT_GRID_STEP_B,
    DEFAULT_GRID_STEP_K,
    DEFAULT_K_MAX,
    DEFAULT_K_MIN,
    DEFAULT_MANUAL_B,
    DEFAULT_MANUAL_K,
    DEFAULT_MAX_MODE,
    DEFAULT_METHOD,
    DEFAULT_SAVE_RESULT,
    DEFAULT_USE_NORMALIZED_MSE,
    DEFAULT_WEIGHT_MODE,
    MAX_SUPPORTED_MODE,
)
from domain.models.search_condition import SearchCondition
from ui.state.session_state_manager import reset_optimization_settings


@dataclass
class SidebarState:
    """
    サイドバー入力状態を保持するデータクラス。
    """

    facility_name: Optional[str]
    cable_no: Optional[str]
    branch_no: Optional[str]

    max_mode: int

    manual_k: float
    manual_b: float

    search_condition: SearchCondition

    save_result: bool
    execute_manual_update: bool
    execute_optimization: bool
    execute_save: bool


def render_sidebar(
    facility_names: list[str],
    cable_numbers: list[str],
    branch_numbers: list[str],
) -> SidebarState:
    """
    サイドバーを描画し、入力状態を SidebarState として返す。

    Args:
        facility_names:
            施設名候補一覧。
        cable_numbers:
            選択済み施設名に対応するケーブルNo候補一覧。
        branch_numbers:
            選択済み施設名・ケーブルNoに対応する枝番候補一覧。

    Returns:
        SidebarState:
            サイドバーで入力された状態。
    """
    st.sidebar.header("条件入力")

    facility_name: Optional[str] = _render_selectbox(
        label="施設名",
        options=facility_names,
        key="sidebar_facility_name",
    )

    cable_no: Optional[str] = _render_selectbox(
        label="ケーブルNo.",
        options=cable_numbers,
        key="sidebar_cable_no",
    )

    branch_no: Optional[str] = _render_selectbox(
        label="枝番",
        options=branch_numbers,
        key="sidebar_branch_no",
    )

    st.sidebar.divider()
    st.sidebar.subheader("モード設定")

    max_mode: int = st.sidebar.number_input(
        label="最大次数",
        min_value=1,
        max_value=MAX_SUPPORTED_MODE,
        value=DEFAULT_MAX_MODE,
        step=1,
        key="sidebar_max_mode",
    )

    st.sidebar.divider()
    st.sidebar.subheader("手動検証")

    col_k, col_b = st.sidebar.columns(2)

    manual_k_str: str = col_k.text_input(
        label="k：張力の係数",
        value=f"{DEFAULT_MANUAL_K:.2f}",
        key="sidebar_manual_k",
    )

    manual_b_str: str = col_b.text_input(
        label="b：EIの係数(β)",
        value=f"{DEFAULT_MANUAL_B:.2f}",
        key="sidebar_manual_b",
    )

    try:
        manual_k: float = float(manual_k_str)
    except ValueError:
        manual_k = float(DEFAULT_MANUAL_K)

    try:
        manual_b: float = float(manual_b_str)
    except ValueError:
        manual_b = float(DEFAULT_MANUAL_B)

    execute_manual_update: bool = st.sidebar.button(
        label="理論周波数更新",
        use_container_width=True,
        key="sidebar_execute_manual_update",
    )

    st.sidebar.divider()
    st.sidebar.subheader("探索設定")

    current_key = (facility_name, cable_no, branch_no)
    previous_key = st.session_state.get("current_sidebar_key")

    if previous_key != current_key:
        reset_optimization_settings()
        st.session_state["current_sidebar_key"] = current_key


    method: str = st.sidebar.selectbox(
        label="探索方法",
        options=["grid", "scipy"],
        index=0 if DEFAULT_METHOD == "grid" else 1,
        key="sidebar_method",
    )

    col_k_min, col_k_max = st.sidebar.columns(2)
    k_min_str: str = col_k_min.text_input(
        label="k_min",
        value=f"{DEFAULT_K_MIN:.1f}",
        key="sidebar_k_min",
    )
    k_max_str: str = col_k_max.text_input(
        label="k_max",
        value=f"{DEFAULT_K_MAX:.1f}",
        key="sidebar_k_max",
    )

    col_b_min, col_b_max = st.sidebar.columns(2)
    b_min_str: str = col_b_min.text_input(
        label="b_min",
        value=f"{DEFAULT_B_MIN:.1f}",
        key="sidebar_b_min",
    )
    b_max_str: str = col_b_max.text_input(
        label="b_max",
        value=f"{DEFAULT_B_MAX:.1f}",
        key="sidebar_b_max",
    )

    if method == "grid":
        col_step_k, col_step_b = st.sidebar.columns(2)
        grid_step_k_str: str = col_step_k.text_input(
            label="grid_step_k",
            value=f"{DEFAULT_GRID_STEP_K:.3f}",
            key="sidebar_grid_step_k",
        )
        grid_step_b_str: str = col_step_b.text_input(
            label="grid_step_b",
            value=f"{DEFAULT_GRID_STEP_B:.3f}",
            key="sidebar_grid_step_b",
        )
    else:
        grid_step_k_str = f"{DEFAULT_GRID_STEP_K:.3f}"
        grid_step_b_str = f"{DEFAULT_GRID_STEP_B:.3f}"

    try:
        k_min: float = float(k_min_str)
    except ValueError:
        k_min = float(DEFAULT_K_MIN)

    try:
        k_max: float = float(k_max_str)
    except ValueError:
        k_max = float(DEFAULT_K_MAX)

    try:
        b_min: float = float(b_min_str)
    except ValueError:
        b_min = float(DEFAULT_B_MIN)

    try:
        b_max: float = float(b_max_str)
    except ValueError:
        b_max = float(DEFAULT_B_MAX)

    try:
        grid_step_k: float = float(grid_step_k_str)
    except ValueError:
        grid_step_k = float(DEFAULT_GRID_STEP_K)

    try:
        grid_step_b: float = float(grid_step_b_str)
    except ValueError:
        grid_step_b = float(DEFAULT_GRID_STEP_B)

    execute_optimization: bool = st.sidebar.button(
        label="最適化実行",
        use_container_width=True,
        key="sidebar_execute_optimization",
    )

    st.sidebar.divider()
    st.sidebar.subheader("誤差評価")

    weight_mode: str = st.sidebar.selectbox(
        label="重み付け",
        options=["none", "mode_number", "manual"],
        index=_get_weight_mode_index(DEFAULT_WEIGHT_MODE),
        key="sidebar_weight_mode",
    )

    use_normalized_mse: bool = st.sidebar.checkbox(
        label="normalized MSE を使う",
        value=DEFAULT_USE_NORMALIZED_MSE,
        key="sidebar_use_normalized_mse",
    )

    st.sidebar.divider()
    st.sidebar.subheader("保存")

    save_result: bool = st.sidebar.checkbox(
        label="結果保存",
        value=DEFAULT_SAVE_RESULT,
        key="sidebar_save_result",
    )

    execute_save: bool = st.sidebar.button(
        label="保存",
        use_container_width=True,
        disabled=not save_result,
        key="sidebar_execute_save",
    )

    search_condition = SearchCondition(
        method=method,
        k_min=float(k_min),
        k_max=float(k_max),
        b_min=float(b_min),
        b_max=float(b_max),
        grid_step_k=float(grid_step_k),
        grid_step_b=float(grid_step_b),
        weight_mode=weight_mode,
        manual_weights=None,
        use_normalized_mse=bool(use_normalized_mse),
    )


    return SidebarState(
        facility_name=facility_name,
        cable_no=cable_no,
        branch_no=branch_no,
        max_mode=int(max_mode),
        manual_k=manual_k,
        manual_b=manual_b,
        search_condition=search_condition,
        save_result=bool(save_result),
        execute_manual_update=bool(execute_manual_update),
        execute_optimization=bool(execute_optimization),
        execute_save=bool(execute_save),
    )


def _render_selectbox(
    label: str,
    options: list[str],
    key: str,
) -> Optional[str]:
    """
    候補が空の場合に None を返す selectbox ラッパー。

    Args:
        label:
            表示ラベル。
        options:
            候補一覧。
        key:
            Streamlit widget key。

    Returns:
        Optional[str]:
            選択値。候補が空なら None。
    """
    if len(options) == 0:
        st.sidebar.selectbox(
            label=label,
            options=["-"],
            index=0,
            disabled=True,
            key=key,
        )
        return None

    return st.sidebar.selectbox(
        label=label,
        options=options,
        index=0,
        key=key,
    )


def _get_weight_mode_index(default_weight_mode: str) -> int:
    """
    重み付け方式のデフォルトindexを返す。

    Args:
        default_weight_mode:
            デフォルトの重み付け方式。

    Returns:
        int:
            selectbox 用 index。
    """
    options: list[str] = ["none", "mode_number", "manual"]
    if default_weight_mode in options:
        return options.index(default_weight_mode)
    return 0