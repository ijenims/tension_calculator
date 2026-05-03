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

CONDITION_INPUT_SIGNATURE_KEY = "_sidebar_condition_input_signature"


@dataclass
class SidebarState:
    """
    サイドバー入力値を保持する UI 状態オブジェクト。

    このクラスは widget の入力結果を app.py に受け渡すためだけに使う。
    業務ロジック上の探索条件オブジェクトは保持しない。
    """

    facility_name: Optional[str]
    cable_no: Optional[str]
    branch_no: Optional[str]

    max_mode: int

    manual_k: float
    manual_b: float

    method: str
    k_min: float
    k_max: float
    b_min: float
    b_max: float
    grid_step_k: float
    grid_step_b: float
    weight_mode: str
    use_normalized_mse: bool

    save_result: bool
    execute_manual_update: bool
    execute_optimization: bool
    reset_search_settings: bool

    surface_z_cap_max: Optional[float]
    surface_view_mode: str


def render_sidebar(
    facility_names: list[str],
    cable_numbers: list[str],
    branch_numbers: list[str],
) -> SidebarState:
    """
    サイドバーを描画し、入力値を SidebarState として返す。

    設計方針:
        - case 選択は通常 widget
        - 手動検証は form 内で submit 時のみ確定
        - 探索方法は form 外に置き、切替時に即 rerun させる
        - 探索設定リセットは明示ボタンで行う
        - widget key を唯一の表示状態とし、二重管理を避ける
    """
    _initialize_sidebar_state()

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

    _maybe_reset_surface_z_cap_on_condition_input_change(
        facility_name=facility_name,
        cable_no=cable_no,
        branch_no=branch_no,
    )

    st.sidebar.subheader("モード設定")

    max_mode: int = int(
        st.sidebar.number_input(
            label="最大次数",
            min_value=1,
            max_value=MAX_SUPPORTED_MODE,
            value=DEFAULT_MAX_MODE,
            step=1,
            key="sidebar_max_mode",
        )
    )

    # -------------------------
    # 手動検証
    # -------------------------
    st.sidebar.divider()
    st.sidebar.subheader("手動検証")

    execute_manual_update: bool = False

    with st.sidebar.form("manual_update_form", clear_on_submit=False):
        col_k, col_b = st.columns(2)

        manual_k_str: str = col_k.text_input(
            label="k：張力の係数",
            key="sidebar_manual_k",
        )

        manual_b_str: str = col_b.text_input(
            label="b：EIの係数(β)",
            key="sidebar_manual_b",
        )

        execute_manual_update = st.form_submit_button(
            label="理論周波数更新",
            width='stretch',
        )

    manual_k: float = _parse_float(manual_k_str, DEFAULT_MANUAL_K)
    manual_b: float = _parse_float(manual_b_str, DEFAULT_MANUAL_B)

    # -------------------------
    # 探索設定
    # -------------------------
    st.sidebar.divider()
    st.sidebar.subheader("探索設定")

    reset_search_settings: bool = st.sidebar.button(
        label="デフォルト値に戻す",
        width='stretch',
        key="sidebar_reset_search_settings",
    )

    if reset_search_settings:
        _reset_search_widget_state()

    method: str = st.sidebar.selectbox(
        label="探索方法",
        options=["grid", "scipy"],
        index=_get_method_index(st.session_state["sidebar_search_method"]),
        key="sidebar_search_method",
    )

    execute_optimization: bool = False

    with st.sidebar.form("search_condition_form", clear_on_submit=False):
        col_k_min, col_b_min = st.columns(2)
        k_min_str: str = col_k_min.text_input(
            label="k_min",
            key="sidebar_k_min",
        )
        b_min_str: str = col_b_min.text_input(
            label="b_min",
            key="sidebar_b_min",
        )

        col_k_max, col_b_max = st.columns(2)
        k_max_str: str = col_k_max.text_input(
            label="k_max",
            key="sidebar_k_max",
        )
        b_max_str: str = col_b_max.text_input(
            label="b_max",
            key="sidebar_b_max",
        )

        if method == "grid":
            col_step_k, col_step_b = st.columns(2)
            grid_step_k_str: str = col_step_k.text_input(
                label="grid_step_k",
                key="sidebar_grid_step_k",
                disabled=(method != "grid"),
            )
            grid_step_b_str: str = col_step_b.text_input(
                label="grid_step_b",
                key="sidebar_grid_step_b",
                disabled=(method != "grid"),
            )
        else:
            grid_step_k_str = st.session_state["sidebar_grid_step_k"]
            grid_step_b_str = st.session_state["sidebar_grid_step_b"]

        weight_mode: str = st.selectbox(
            label="重み付け",
            options=["none", "mode_number", "manual"],
            index=_get_weight_mode_index(st.session_state["sidebar_weight_mode"]),
            key="sidebar_weight_mode",
        )

        use_normalized_mse: bool = st.checkbox(
            label="normalized MSE を使う",
            key="sidebar_use_normalized_mse",
        )

        execute_optimization = st.form_submit_button(
            type="primary",
            label="最適化実行",
            width='stretch',
        )

    k_min: float = _parse_float(k_min_str, DEFAULT_K_MIN)
    k_max: float = _parse_float(k_max_str, DEFAULT_K_MAX)
    b_min: float = _parse_float(b_min_str, DEFAULT_B_MIN)
    b_max: float = _parse_float(b_max_str, DEFAULT_B_MAX)
    grid_step_k: float = _parse_float(grid_step_k_str, DEFAULT_GRID_STEP_K)
    grid_step_b: float = _parse_float(grid_step_b_str, DEFAULT_GRID_STEP_B)

    st.sidebar.divider()
    with st.sidebar.expander("3D サーフェス（grid）", expanded=False):
        _surface_labels: dict[str, str] = {
            "coarse": "全体（粗）",
            "zoom": "最小付近（細）",
        }
        surface_view_mode: str = st.radio(
            label="3D表示領域",
            options=list(_surface_labels.keys()),
            format_func=lambda k: _surface_labels[k],
            horizontal=True,
            key="sidebar_surface_view_mode",
        )

        surface_z_cap_str: str = st.text_input(
            label="MSE 表示上限（空欄＝自動・1e9未満のみで99%分位）",
            key="sidebar_surface_z_cap",
            placeholder="例: 0.05",
        )

    surface_z_cap_max: Optional[float] = _parse_optional_positive_float(surface_z_cap_str)

    # -------------------------
    # 保存
    # -------------------------
    st.sidebar.divider()
    st.sidebar.subheader("保存")

    save_result: bool = st.sidebar.checkbox(
        label="結果保存",
        value=DEFAULT_SAVE_RESULT,
        key="sidebar_save_result",
    )

    return SidebarState(
        facility_name=facility_name,
        cable_no=cable_no,
        branch_no=branch_no,
        max_mode=max_mode,
        manual_k=manual_k,
        manual_b=manual_b,
        method=method,
        k_min=k_min,
        k_max=k_max,
        b_min=b_min,
        b_max=b_max,
        grid_step_k=grid_step_k,
        grid_step_b=grid_step_b,
        weight_mode=weight_mode,
        use_normalized_mse=use_normalized_mse,
        save_result=save_result,
        execute_manual_update=execute_manual_update,
        execute_optimization=execute_optimization,
        reset_search_settings=reset_search_settings,
        surface_z_cap_max=surface_z_cap_max,
        surface_view_mode=surface_view_mode,
    )


def _maybe_reset_surface_z_cap_on_condition_input_change(
    facility_name: Optional[str],
    cable_no: Optional[str],
    branch_no: Optional[str],
) -> None:
    """
    「条件入力」（施設・ケーブルNo・枝番）が変わったら、3D 用 MSE 上限の手入力を空に戻す。
    """
    sig: tuple[Optional[str], Optional[str], Optional[str]] = (
        facility_name,
        cable_no,
        branch_no,
    )
    prev: Optional[tuple[Optional[str], Optional[str], Optional[str]]] = st.session_state.get(
        CONDITION_INPUT_SIGNATURE_KEY
    )
    st.session_state[CONDITION_INPUT_SIGNATURE_KEY] = sig
    if prev is not None and prev != sig:
        st.session_state["sidebar_surface_z_cap"] = ""


def _initialize_sidebar_state() -> None:
    """
    sidebar 用 widget state を初期化する。

    widget key 自体を唯一の表示状態として使うため、
    初期値はここで一度だけ投入する。
    """
    defaults: dict[str, object] = {
        "sidebar_manual_k": f"{DEFAULT_MANUAL_K:.2f}",
        "sidebar_manual_b": f"{DEFAULT_MANUAL_B:.2f}",
        "sidebar_search_method": DEFAULT_METHOD,
        "sidebar_k_min": f"{DEFAULT_K_MIN:.1f}",
        "sidebar_k_max": f"{DEFAULT_K_MAX:.1f}",
        "sidebar_b_min": f"{DEFAULT_B_MIN:.1f}",
        "sidebar_b_max": f"{DEFAULT_B_MAX:.1f}",
        "sidebar_grid_step_k": f"{DEFAULT_GRID_STEP_K:.3f}",
        "sidebar_grid_step_b": f"{DEFAULT_GRID_STEP_B:.3f}",
        "sidebar_weight_mode": DEFAULT_WEIGHT_MODE,
        "sidebar_use_normalized_mse": DEFAULT_USE_NORMALIZED_MSE,
        "sidebar_surface_z_cap": "",
        "sidebar_surface_view_mode": "coarse",
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def _reset_search_widget_state() -> None:
    """
    探索設定 widget の表示値をデフォルトに戻す。

    注意:
        reset 対象は探索設定のみ。
        手動検証の k, b はここでは触らない。
    """
    st.session_state["sidebar_search_method"] = DEFAULT_METHOD
    st.session_state["sidebar_k_min"] = f"{DEFAULT_K_MIN:.1f}"
    st.session_state["sidebar_k_max"] = f"{DEFAULT_K_MAX:.1f}"
    st.session_state["sidebar_b_min"] = f"{DEFAULT_B_MIN:.1f}"
    st.session_state["sidebar_b_max"] = f"{DEFAULT_B_MAX:.1f}"
    st.session_state["sidebar_grid_step_k"] = f"{DEFAULT_GRID_STEP_K:.3f}"
    st.session_state["sidebar_grid_step_b"] = f"{DEFAULT_GRID_STEP_B:.3f}"
    st.session_state["sidebar_weight_mode"] = DEFAULT_WEIGHT_MODE
    st.session_state["sidebar_use_normalized_mse"] = DEFAULT_USE_NORMALIZED_MSE


def _render_selectbox(
    label: str,
    options: list[str],
    key: str,
) -> Optional[str]:
    """
    先頭にプレースホルダを出し、未選択なら None を返す。
    """
    placeholder = "選択してください"

    if len(options) == 0:
        st.sidebar.selectbox(
            label=label,
            options=[placeholder],
            index=0,
            disabled=True,
            key=key,
        )
        return None

    display_options = [placeholder] + options

    selected: str = st.sidebar.selectbox(
        label=label,
        options=display_options,
        index=0,
        key=key,
    )

    if selected == placeholder:
        return None

    return selected


def _parse_optional_positive_float(value: str) -> Optional[float]:
    """
    空・空白は None。正の float ならその値。それ以外は None。
    """
    stripped: str = value.strip()
    if not stripped:
        return None
    try:
        parsed: float = float(stripped)
    except ValueError:
        return None
    if parsed <= 0:
        return None
    return parsed


def _parse_float(value: str, default: float) -> float:
    """
    文字列を float に変換する。

    変換できない場合は default を返す。
    """
    try:
        return float(value)
    except ValueError:
        return float(default)


def _get_method_index(method: str) -> int:
    """
    探索方法の index を返す。
    """
    options: list[str] = ["grid", "scipy"]
    if method in options:
        return options.index(method)
    return 0


def _get_weight_mode_index(weight_mode: str) -> int:
    """
    重み付け方式の index を返す。
    """
    options: list[str] = ["none", "mode_number", "manual"]
    if weight_mode in options:
        return options.index(weight_mode)
    return 0