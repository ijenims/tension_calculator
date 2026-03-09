from typing import Optional

import numpy as np
import streamlit as st

from config.defaults import DEFAULT_MANUAL_B, DEFAULT_MANUAL_K, DEFAULT_MAX_MODE
from domain.models.calculation_result import CalculationResult


def initialize_session_state() -> None:
    """
    session_state の初期値を設定する。
    既に存在するキーは上書きしない。
    """
    defaults: dict = {
        "selected_facility_name": None,
        "selected_cable_no": None,
        "selected_branch_no": None,
        "max_mode": DEFAULT_MAX_MODE,
        "manual_k": float(DEFAULT_MANUAL_K),
        "manual_b": float(DEFAULT_MANUAL_B),
        "measured_frequencies_hz": [],
        "use_mask": [],
        "theoretical_frequencies_hz": [],
        "last_result": None,
        "surface_K": None,
        "surface_B": None,
        "surface_Z": None,
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def set_selected_keys(
    facility_name: Optional[str],
    cable_no: Optional[str],
    branch_no: Optional[str],
) -> None:
    """
    選択中の識別キーを session_state に保存する。
    """
    st.session_state["selected_facility_name"] = facility_name
    st.session_state["selected_cable_no"] = cable_no
    st.session_state["selected_branch_no"] = branch_no


def get_selected_keys() -> tuple[Optional[str], Optional[str], Optional[str]]:
    """
    session_state から選択中の識別キーを取得する。
    """
    return (
        st.session_state.get("selected_facility_name"),
        st.session_state.get("selected_cable_no"),
        st.session_state.get("selected_branch_no"),
    )


def set_manual_parameters(
    manual_k: float,
    manual_b: float,
    max_mode: int,
) -> None:
    """
    手動パラメータを session_state に保存する。
    """
    st.session_state["manual_k"] = float(manual_k)
    st.session_state["manual_b"] = float(manual_b)
    st.session_state["max_mode"] = int(max_mode)


def set_frequency_state(
    measured_frequencies_hz: list[float | None],
    use_mask: list[bool],
    theoretical_frequencies_hz: list[float],
) -> None:
    """
    周波数編集状態を session_state に保存する。
    """
    st.session_state["measured_frequencies_hz"] = measured_frequencies_hz
    st.session_state["use_mask"] = use_mask
    st.session_state["theoretical_frequencies_hz"] = theoretical_frequencies_hz


def get_frequency_state() -> tuple[list[float | None], list[bool], list[float]]:
    """
    session_state から周波数編集状態を取得する。
    """
    return (
        st.session_state.get("measured_frequencies_hz", []),
        st.session_state.get("use_mask", []),
        st.session_state.get("theoretical_frequencies_hz", []),
    )


def set_last_result(result: Optional[CalculationResult]) -> None:
    """
    最新計算結果を session_state に保存する。
    """
    st.session_state["last_result"] = result


def get_last_result() -> Optional[CalculationResult]:
    """
    最新計算結果を session_state から取得する。
    """
    return st.session_state.get("last_result")


def set_surface_data(
    K: Optional[np.ndarray],
    B: Optional[np.ndarray],
    Z: Optional[np.ndarray],
) -> None:
    """
    3Dサーフェス描画用データを session_state に保存する。
    """
    st.session_state["surface_K"] = K
    st.session_state["surface_B"] = B
    st.session_state["surface_Z"] = Z


def get_surface_data() -> tuple[Optional[np.ndarray], Optional[np.ndarray], Optional[np.ndarray]]:
    """
    3Dサーフェス描画用データを session_state から取得する。
    """
    return (
        st.session_state.get("surface_K"),
        st.session_state.get("surface_B"),
        st.session_state.get("surface_Z"),
    )


def clear_surface_data() -> None:
    """
    3Dサーフェス描画用データをクリアする。
    """
    st.session_state["surface_K"] = None
    st.session_state["surface_B"] = None
    st.session_state["surface_Z"] = None


def reset_case_state(current_key: tuple) -> None:
    """
    選択中ケーブルが変わったときに、ケース依存の session_state を初期化する。
    """
    previous_key = st.session_state.get("current_cable_key")

    if previous_key != current_key:
        st.session_state["current_cable_key"] = current_key
        st.session_state["measured_frequencies_hz"] = []
        st.session_state["use_mask"] = []
        st.session_state["theoretical_frequencies_hz"] = []
        st.session_state["last_result"] = None
        st.session_state["surface_K"] = None
        st.session_state["surface_B"] = None
        st.session_state["surface_Z"] = None
        