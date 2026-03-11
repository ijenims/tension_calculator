from typing import Optional

import numpy as np
import streamlit as st

from config.defaults import (
    DEFAULT_MANUAL_B,
    DEFAULT_MANUAL_K,
    DEFAULT_MAX_MODE,
)
from domain.models.calculation_result import CalculationResult
from domain.models.search_condition import SearchCondition


SEARCH_CONDITION_KEY = "search_condition"
CASE_KEY_KEY = "case_key"

LAST_RESULT_KEY = "last_result"
SURFACE_K_KEY = "surface_K"
SURFACE_B_KEY = "surface_B"
SURFACE_Z_KEY = "surface_Z"

EDITOR_MEASURED_KEY = "editor_measured"
EDITOR_USE_MASK_KEY = "editor_use_mask"
EDITOR_THEORETICAL_KEY = "editor_theoretical"

SELECTED_FACILITY_KEY = "selected_facility_name"
SELECTED_CABLE_KEY = "selected_cable_no"
SELECTED_BRANCH_KEY = "selected_branch_no"

MANUAL_K_KEY = "manual_k"
MANUAL_B_KEY = "manual_b"
MAX_MODE_KEY = "max_mode"


def initialize_session_state() -> None:
    """
    session_state の初期値を設定する。

    この関数はアプリ起動時に一度呼ばれることを想定しており、
    既に値が存在するキーは上書きしない。

    管理対象は次の3系統。
    1. 業務状態:
       - SearchCondition
       - 選択中 case_key
    2. 計算結果:
       - last_result
       - 3D surface 用データ
    3. UI補助状態:
       - 周波数編集内容
       - 手動入力パラメータ
       - 現在の選択キー
    """
    defaults: dict[str, object] = {
        SEARCH_CONDITION_KEY: SearchCondition.default(),
        CASE_KEY_KEY: None,
        LAST_RESULT_KEY: None,
        SURFACE_K_KEY: None,
        SURFACE_B_KEY: None,
        SURFACE_Z_KEY: None,
        EDITOR_MEASURED_KEY: [],
        EDITOR_USE_MASK_KEY: [],
        EDITOR_THEORETICAL_KEY: [],
        SELECTED_FACILITY_KEY: None,
        SELECTED_CABLE_KEY: None,
        SELECTED_BRANCH_KEY: None,
        MANUAL_K_KEY: float(DEFAULT_MANUAL_K),
        MANUAL_B_KEY: float(DEFAULT_MANUAL_B),
        MAX_MODE_KEY: int(DEFAULT_MAX_MODE),
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def get_case_key() -> Optional[tuple[Optional[str], Optional[str], Optional[str]]]:
    """
    現在の case_key を取得する。

    Returns:
        Optional[tuple[Optional[str], Optional[str], Optional[str]]]:
            (facility_name, cable_no, branch_no)
            未設定の場合は None。
    """
    return st.session_state.get(CASE_KEY_KEY)


def set_case_key(
    facility_name: Optional[str],
    cable_no: Optional[str],
    branch_no: Optional[str],
) -> None:
    """
    現在の case_key を保存する。

    Args:
        facility_name:
            施設名。
        cable_no:
            ケーブルNo。
        branch_no:
            枝番。
    """
    st.session_state[CASE_KEY_KEY] = (facility_name, cable_no, branch_no)


def reset_search_condition() -> SearchCondition:
    """
    SearchCondition をデフォルト値で再生成し、session_state に保存する。

    Returns:
        SearchCondition:
            再生成されたデフォルト探索条件。
    """
    condition = SearchCondition.default()
    st.session_state[SEARCH_CONDITION_KEY] = condition
    return condition


def get_search_condition() -> SearchCondition:
    """
    現在の SearchCondition を取得する。

    未初期化時は default() で生成して保存する。

    Returns:
        SearchCondition:
            現在の探索条件。
    """
    condition = st.session_state.get(SEARCH_CONDITION_KEY)

    if condition is None:
        condition = SearchCondition.default()
        st.session_state[SEARCH_CONDITION_KEY] = condition

    return condition


def set_search_condition(condition: SearchCondition) -> None:
    """
    SearchCondition を session_state に保存する。

    Args:
        condition:
            保存対象の探索条件。
    """
    st.session_state[SEARCH_CONDITION_KEY] = condition


def update_case_and_reset_search_if_needed(
    facility_name: Optional[str],
    cable_no: Optional[str],
    branch_no: Optional[str],
) -> bool:
    """
    case_key の変化を検知し、変化があれば探索条件をデフォルトに戻す。

    facility / cable / branch のいずれか1つでも変わった場合、
    SearchCondition を丸ごとリセットする。

    Args:
        facility_name:
            現在の施設名。
        cable_no:
            現在のケーブルNo。
        branch_no:
            現在の枝番。

    Returns:
        bool:
            case_key が変化した場合 True、変化なしなら False。
    """
    current_key = (facility_name, cable_no, branch_no)
    previous_key = get_case_key()

    if previous_key != current_key:
        set_case_key(
            facility_name=facility_name,
            cable_no=cable_no,
            branch_no=branch_no,
        )
        reset_search_condition()
        return True

    return False


def set_selected_keys(
    facility_name: Optional[str],
    cable_no: Optional[str],
    branch_no: Optional[str],
) -> None:
    """
    選択中の識別キーを保存する。

    Args:
        facility_name:
            施設名。
        cable_no:
            ケーブルNo。
        branch_no:
            枝番。
    """
    st.session_state[SELECTED_FACILITY_KEY] = facility_name
    st.session_state[SELECTED_CABLE_KEY] = cable_no
    st.session_state[SELECTED_BRANCH_KEY] = branch_no


def get_selected_keys() -> tuple[Optional[str], Optional[str], Optional[str]]:
    """
    選択中の識別キーを取得する。

    Returns:
        tuple[Optional[str], Optional[str], Optional[str]]:
            (facility_name, cable_no, branch_no)
    """
    return (
        st.session_state.get(SELECTED_FACILITY_KEY),
        st.session_state.get(SELECTED_CABLE_KEY),
        st.session_state.get(SELECTED_BRANCH_KEY),
    )


def set_manual_parameters(
    manual_k: float,
    manual_b: float,
    max_mode: int,
) -> None:
    """
    手動検証用パラメータを保存する。

    Args:
        manual_k:
            手動張力係数。
        manual_b:
            手動剛性係数。
        max_mode:
            最大次数。
    """
    st.session_state[MANUAL_K_KEY] = float(manual_k)
    st.session_state[MANUAL_B_KEY] = float(manual_b)
    st.session_state[MAX_MODE_KEY] = int(max_mode)


def set_frequency_state(
    measured_frequencies_hz: list[float | None],
    use_mask: list[bool],
    theoretical_frequencies_hz: list[float],
) -> None:
    """
    周波数編集状態を保存する。

    Args:
        measured_frequencies_hz:
            実測周波数列。
        use_mask:
            使用モードフラグ列。
        theoretical_frequencies_hz:
            理論周波数列。
    """
    st.session_state[EDITOR_MEASURED_KEY] = measured_frequencies_hz
    st.session_state[EDITOR_USE_MASK_KEY] = use_mask
    st.session_state[EDITOR_THEORETICAL_KEY] = theoretical_frequencies_hz


def get_frequency_state() -> tuple[list[float | None], list[bool], list[float]]:
    """
    周波数編集状態を取得する。

    Returns:
        tuple[list[float | None], list[bool], list[float]]:
            (実測周波数列, 使用モード列, 理論周波数列)
    """
    return (
        st.session_state.get(EDITOR_MEASURED_KEY, []),
        st.session_state.get(EDITOR_USE_MASK_KEY, []),
        st.session_state.get(EDITOR_THEORETICAL_KEY, []),
    )


def set_last_result(result: Optional[CalculationResult]) -> None:
    """
    最新計算結果を保存する。

    Args:
        result:
            保存対象の計算結果。
    """
    st.session_state[LAST_RESULT_KEY] = result


def get_last_result() -> Optional[CalculationResult]:
    """
    最新計算結果を取得する。

    Returns:
        Optional[CalculationResult]:
            最新計算結果。未設定なら None。
    """
    return st.session_state.get(LAST_RESULT_KEY)


def set_surface_data(
    K: Optional[np.ndarray],
    B: Optional[np.ndarray],
    Z: Optional[np.ndarray],
) -> None:
    """
    3Dサーフェス描画用データを保存する。

    Args:
        K:
            k の meshgrid。
        B:
            b の meshgrid。
        Z:
            各格子点の目的関数値。
    """
    st.session_state[SURFACE_K_KEY] = K
    st.session_state[SURFACE_B_KEY] = B
    st.session_state[SURFACE_Z_KEY] = Z


def get_surface_data() -> tuple[Optional[np.ndarray], Optional[np.ndarray], Optional[np.ndarray]]:
    """
    3Dサーフェス描画用データを取得する。

    Returns:
        tuple[Optional[np.ndarray], Optional[np.ndarray], Optional[np.ndarray]]:
            (K, B, Z)
    """
    return (
        st.session_state.get(SURFACE_K_KEY),
        st.session_state.get(SURFACE_B_KEY),
        st.session_state.get(SURFACE_Z_KEY),
    )


def clear_surface_data() -> None:
    """
    3Dサーフェス描画用データをクリアする。
    """
    st.session_state[SURFACE_K_KEY] = None
    st.session_state[SURFACE_B_KEY] = None
    st.session_state[SURFACE_Z_KEY] = None


def reset_result_state() -> None:
    """
    計算結果系の状態をクリアする。

    クリア対象:
        - 最新計算結果
        - 3D surface 用データ
    """
    set_last_result(None)
    clear_surface_data()


def reset_frequency_state() -> None:
    """
    周波数編集状態をクリアする。
    """
    st.session_state[EDITOR_MEASURED_KEY] = []
    st.session_state[EDITOR_USE_MASK_KEY] = []
    st.session_state[EDITOR_THEORETICAL_KEY] = []