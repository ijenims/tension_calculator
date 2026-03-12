from typing import Optional

import streamlit as st

from config.defaults import APP_TITLE, MASTER_FILEPATH, RESULT_FILEPATH, RESULT_SHEET_NAME, MASTER_SHEET_NAME
from domain.models.calculation_result import CalculationResult
from domain.physics.frequency_formula import FrequencyFormula
from infrastructure.repositories.excel_cable_repository import ExcelCableRepository
from infrastructure.repositories.excel_result_repository import ExcelResultRepository
from services.manual_frequency_service import ManualFrequencyService
from services.optimization_service import OptimizationService
from ui.components.spec_panel import render_spec_panel
from ui.components.frequency_editor import render_frequency_editor
from ui.components.result_panel import render_result_panel
from ui.components.save_panel import render_save_panel
from ui.components.sidebar import SidebarState, render_sidebar
from ui.state.session_state_manager import (
    clear_surface_data,
    get_frequency_state,
    get_last_result,
    get_surface_data,
    initialize_session_state,
    set_frequency_state,
    set_last_result,
    set_manual_parameters,
    set_selected_keys,
    set_surface_data,
)
from visualization.frequency_plot import create_frequency_plot
from visualization.objective_surface_plot import create_objective_surface_plot
from visualization.residual_plot import create_residual_plot


def main() -> None:
    """
    張力計算 Web アプリのエントリポイント。
    """
    st.set_page_config(
        page_title=APP_TITLE,
        layout="wide",
    )
    st.title(APP_TITLE)

    initialize_session_state()

    cable_repository = ExcelCableRepository(
        filepath=MASTER_FILEPATH,
        sheet_name=MASTER_SHEET_NAME,
        )
    result_repository = ExcelResultRepository(
        filepath=RESULT_FILEPATH,
        sheet_name=RESULT_SHEET_NAME,
    )
    manual_service = ManualFrequencyService()
    optimization_service = OptimizationService()

    facility_names: list[str] = cable_repository.get_facility_names()

    sidebar_state: SidebarState = render_sidebar(
        facility_names=facility_names,
        cable_numbers=_get_cable_numbers(cable_repository, facility_names),
        branch_numbers=_get_branch_numbers(cable_repository, facility_names),
    )

    from ui.state.session_state_manager import (
        get_search_condition,
    )


    # ② SearchCondition取得
    search_condition = get_search_condition()

    # ③ Sidebar入力を反映
    search_condition.method = sidebar_state.method
    search_condition.k_min = sidebar_state.k_min
    search_condition.k_max = sidebar_state.k_max
    search_condition.b_min = sidebar_state.b_min
    search_condition.b_max = sidebar_state.b_max
    search_condition.grid_step_k = sidebar_state.grid_step_k
    search_condition.grid_step_b = sidebar_state.grid_step_b
    search_condition.weight_mode = sidebar_state.weight_mode
    search_condition.use_normalized_mse = sidebar_state.use_normalized_mse

    current_key = (
        sidebar_state.facility_name,
        sidebar_state.cable_no,
        sidebar_state.branch_no,
        sidebar_state.max_mode,
    )

    set_selected_keys(
        facility_name=sidebar_state.facility_name,
        cable_no=sidebar_state.cable_no,
        branch_no=sidebar_state.branch_no,
    )

    set_manual_parameters(
        manual_k=sidebar_state.manual_k,
        manual_b=sidebar_state.manual_b,
        max_mode=sidebar_state.max_mode,
    )

    if not _is_selection_complete(sidebar_state):
        st.info("施設名・ケーブルNo.・枝番を選択してくれ。")
        render_result_panel(None)
        return

    cable = cable_repository.get_cable_record(
        facility_name=sidebar_state.facility_name,  # type: ignore[arg-type]
        cable_no=sidebar_state.cable_no,            # type: ignore[arg-type]
        branch_no=sidebar_state.branch_no,          # type: ignore[arg-type]
        max_mode=sidebar_state.max_mode,
    )

    current_key = (
        sidebar_state.facility_name,
        sidebar_state.cable_no,
        sidebar_state.branch_no,
        sidebar_state.max_mode,
    )

    previous_key = st.session_state.get("current_cable_key")
    is_new_case = previous_key != current_key

    if is_new_case:
        st.session_state["current_cable_key"] = current_key

        initial_measured = cable.measured_frequencies_hz
        initial_use_mask = [freq is not None for freq in initial_measured]

        design_rigidity = cable.design_rigidity_Nm2
        if design_rigidity is None:
            raise ValueError("design_rigidity_Nm2 is required.")

        initial_theoretical = FrequencyFormula.calculate(
            tension_kN=cable.design_tension_kN * 1.0,
            rigidity_Nm2=design_rigidity * 0.5,
            unit_weight_kg_per_m=cable.unit_weight_kg_per_m,
            cable_length_m=cable.cable_length_m,
            max_mode=cable.max_mode,
        )

        st.session_state["editor_measured"] = initial_measured
        st.session_state["editor_use_mask"] = initial_use_mask
        st.session_state["editor_theoretical"] = initial_theoretical

        set_last_result(None)
        clear_surface_data()

    render_spec_panel(cable)

    edited_measured_frequencies_hz, edited_use_mask = render_frequency_editor(
        case_key=str(current_key),
        theoretical_freqs=st.session_state["editor_theoretical"],
        measured_freqs=st.session_state["editor_measured"],
        use_mask=st.session_state["editor_use_mask"],
    )

    st.session_state["editor_measured"] = edited_measured_frequencies_hz
    st.session_state["editor_use_mask"] = edited_use_mask

    working_cable = _clone_cable_with_edited_frequencies(
        cable=cable,
        measured_frequencies_hz=edited_measured_frequencies_hz,
    )

    result: Optional[CalculationResult] = get_last_result()

    if sidebar_state.execute_manual_update:
        try:
            result = manual_service.calculate(
                cable=working_cable,
                k=sidebar_state.manual_k,
                b=sidebar_state.manual_b,
                use_mask=edited_use_mask,
                condition=search_condition,
            )
            set_last_result(result)
            st.session_state["editor_theoretical"] = result.theoretical_frequencies_hz
            clear_surface_data()
        except Exception as exc:
            st.error(f"理論周波数更新でエラー: {exc}")

    elif sidebar_state.execute_optimization:
        try:
            if search_condition.method == "grid":
                result, K, B, Z = optimization_service.optimize_with_surface(
                    cable=working_cable,
                    use_mask=edited_use_mask,
                    condition=search_condition,
                )
                set_surface_data(K=K, B=B, Z=Z)
            else:
                result = optimization_service.optimize(
                    cable=working_cable,
                    use_mask=edited_use_mask,
                    condition=search_condition,
                )
                clear_surface_data()

            set_last_result(result)
            st.session_state["editor_theoretical"] = result.theoretical_frequencies_hz
        except Exception as exc:
            st.error(f"最適化実行でエラー: {exc}")

    st.divider()

    result = get_last_result()
    render_result_panel(result)

    if result is not None:
        try:
            freq_fig = create_frequency_plot(
                measured_frequencies_hz=result.measured_frequencies_hz,
                theoretical_frequencies_hz=result.theoretical_frequencies_hz,
                use_mask=result.use_mask,
            )            

            residual_fig = create_residual_plot(
                measured_frequencies_hz=result.measured_frequencies_hz,
                theoretical_frequencies_hz=result.theoretical_frequencies_hz,
                use_mask=result.use_mask,
            )

            st.divider()

            col_left, col_right = st.columns(2)
            with col_left:
                st.plotly_chart(freq_fig, width="stretch")
            with col_right:
                st.plotly_chart(residual_fig, width="stretch")

            st.divider()
                
        except Exception as exc:
            st.error(f"グラフ描画でエラー: {exc}")

        K, B, Z = get_surface_data()
        if (
            search_condition.method == "grid"
            and K is not None
            and B is not None
            and Z is not None
        ):
            try:
                surface_fig = create_objective_surface_plot(
                    K=K,
                    B=B,
                    Z=Z,
                    title="Objective Surface (MSE)",
                    show_contours=True,
                    orthographic=True,
                    aspect_ratio=(1.0, 1.0, 1.0),
                    mark_min=True,
                )
                st.plotly_chart(surface_fig, width="stretch")
            except Exception as exc:
                st.error(f"3Dグラフ描画でエラー: {exc}")

    execute_save: bool = render_save_panel(
        save_enabled=sidebar_state.save_result,
        result=result,
    )

    if execute_save and result is not None:
        try:
            method_label = _build_method_label(
                is_manual_update=sidebar_state.execute_manual_update,
                optimization_method=search_condition.method,
            )
            result_repository.append_result(
                cable=working_cable,
                result=result,
                condition=search_condition,
                method=method_label,
            )
            st.success("結果を保存したで。")
        except Exception as exc:
            st.error(f"保存でエラー: {exc}")


def _get_cable_numbers(
    cable_repository: ExcelCableRepository,
    facility_names: list[str],
) -> list[str]:
    """
    現在の session_state 上の施設名選択に応じてケーブルNo候補を返す。
    """
    selected_facility_name = st.session_state.get("sidebar_facility_name")

    if not facility_names or selected_facility_name is None:
        return []

    return cable_repository.get_cable_numbers(selected_facility_name)


def _get_branch_numbers(
    cable_repository: ExcelCableRepository,
    facility_names: list[str],
) -> list[str]:
    """
    現在の session_state 上の施設名・ケーブルNo選択に応じて枝番候補を返す。
    """
    selected_facility_name = st.session_state.get("sidebar_facility_name")
    selected_cable_no = st.session_state.get("sidebar_cable_no")

    if not facility_names or selected_facility_name is None or selected_cable_no is None:
        return []

    return cable_repository.get_branch_numbers(
        facility_name=selected_facility_name,
        cable_no=selected_cable_no,
    )


def _is_selection_complete(sidebar_state: SidebarState) -> bool:
    """
    ケーブル選択が完了しているかを判定する。
    """
    return all(
        value is not None and str(value) != ""
        for value in [
            sidebar_state.facility_name,
            sidebar_state.cable_no,
            sidebar_state.branch_no,
        ]
    )


def _clone_cable_with_edited_frequencies(
    cable,
    measured_frequencies_hz: list[float | None],
):
    """
    編集後の実測周波数を反映した CableRecord を返す。
    """
    from dataclasses import replace

    return replace(
        cable,
        measured_frequencies_hz=measured_frequencies_hz,
    )


def _build_method_label(
    is_manual_update: bool,
    optimization_method: str,
) -> str:
    """
    保存用の method ラベルを生成する。
    """
    if is_manual_update:
        return "manual"

    if optimization_method == "grid":
        return "optimize_grid"

    if optimization_method == "scipy":
        return "optimize_scipy"

    return "unknown"


if __name__ == "__main__":
    main()