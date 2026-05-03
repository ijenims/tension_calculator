from typing import Callable

import numpy as np

from config.grid_multistage import (
    SURFACE_GRID_STEP_B,
    SURFACE_GRID_STEP_K,
    SURFACE_ZOOM_B_HALF,
    SURFACE_ZOOM_GRID_STEP_B,
    SURFACE_ZOOM_GRID_STEP_K,
    SURFACE_ZOOM_K_HALF,
)
from domain.evaluation.objective_function import objective_function
from domain.models.calculation_result import CalculationResult
from domain.models.cable_record import CableRecord
from domain.models.search_condition import SearchCondition
from domain.physics.frequency_formula import FrequencyFormula
from domain.physics.xi_calculator import XiCalculator
from optimizers.grid_search_optimizer import GridSearchOptimizer
from optimizers.scipy_optimizer import ScipyOptimizer


class OptimizationService:
    """
    最適化サービス。

    CableRecord と SearchCondition を受け取り、
    指定された最適化手法（grid / scipy）で k, b を探索し、
    CalculationResult を生成する。
    """

    def __init__(
        self,
        grid_optimizer: GridSearchOptimizer | None = None,
        scipy_optimizer: ScipyOptimizer | None = None,
    ) -> None:
        """
        Args:
            grid_optimizer:
                グリッドサーチ用 optimizer。
            scipy_optimizer:
                scipy 用 optimizer。
        """
        self._grid_optimizer: GridSearchOptimizer = (
            grid_optimizer if grid_optimizer is not None else GridSearchOptimizer()
        )
        self._scipy_optimizer: ScipyOptimizer = (
            scipy_optimizer if scipy_optimizer is not None else ScipyOptimizer()
        )

    def optimize(
        self,
        cable: CableRecord,
        use_mask: list[bool],
        condition: SearchCondition,
    ) -> CalculationResult:
        """
        最適化を実行し、計算結果を返す。

        Args:
            cable:
                ケーブル諸元および実測周波数を保持するデータ。
            use_mask:
                各モードを比較対象に含めるかどうかのフラグ列。
            condition:
                探索条件。

        Returns:
            CalculationResult:
                最適化結果。

        Raises:
            ValueError:
                設計剛性が未設定の場合。
                use_mask 長が max_mode と一致しない場合。
                method が不正な場合。
        """
        if cable.design_rigidity_Nm2 is None:
            raise ValueError("design_rigidity_Nm2 is required for optimization.")

        if len(use_mask) != cable.max_mode:
            raise ValueError("use_mask length must match cable.max_mode.")

        objective: Callable[[float, float], float] = self._build_objective(
            cable=cable,
            use_mask=use_mask,
            condition=condition,
        )

        if condition.method == "grid":
            k_opt, b_opt, mse_min = self._grid_optimizer.optimize(
                objective_function=objective,
                condition=condition,
            )
        elif condition.method == "scipy":
            k_opt, b_opt, mse_min = self._scipy_optimizer.optimize(
                objective_function=objective,
                condition=condition,
            )
        else:
            raise ValueError(f"Unknown optimization method: {condition.method}")

        return self._build_result(
            cable=cable,
            k=k_opt,
            b=b_opt,
            mse=mse_min,
            use_mask=use_mask,
        )

    def optimize_with_surface(
        self,
        cable: CableRecord,
        use_mask: list[bool],
        condition: SearchCondition,
    ) -> tuple[
        CalculationResult,
        np.ndarray,
        np.ndarray,
        np.ndarray,
        np.ndarray,
        np.ndarray,
        np.ndarray,
    ]:
        """
        グリッドサーチを実行し、結果に加えて 3D 表示用の K, B, Z（全域・粗）と
        最小付近（細）の Kz, Bz, Zz を返す。

        Args:
            cable:
                ケーブル諸元および実測周波数を保持するデータ。
            use_mask:
                各モードを比較対象に含めるかどうかのフラグ列。
            condition:
                探索条件。method は "grid" を想定。

        Returns:
            tuple:
                CalculationResult, K, B, Z（粗・全域）, Kz, Bz, Zz（細・最適解周辺）

        Raises:
            ValueError:
                method が "grid" でない場合。
                設計剛性が未設定の場合。
                use_mask 長が max_mode と一致しない場合。
        """
        if condition.method != "grid":
            raise ValueError("optimize_with_surface is only available for method='grid'.")

        if cable.design_rigidity_Nm2 is None:
            raise ValueError("design_rigidity_Nm2 is required for optimization.")

        if len(use_mask) != cable.max_mode:
            raise ValueError("use_mask length must match cable.max_mode.")

        objective: Callable[[float, float], float] = self._build_objective(
            cable=cable,
            use_mask=use_mask,
            condition=condition,
        )

        k_opt, b_opt, mse_min = self._grid_optimizer.optimize(
            objective_function=objective,
            condition=condition,
        )

        k_mi, k_ma, b_mi, b_ma = self._grid_optimizer.last_search_bounds
        condition_surface = condition.copy()
        condition_surface.k_min = k_mi
        condition_surface.k_max = k_ma
        condition_surface.b_min = b_mi
        condition_surface.b_max = b_ma

        K, B, Z = self._grid_optimizer.evaluate_surface(
            objective_function=objective,
            condition=condition_surface,
            grid_step_k=SURFACE_GRID_STEP_K,
            grid_step_b=SURFACE_GRID_STEP_B,
        )

        k_z_lo = max(k_mi, k_opt - SURFACE_ZOOM_K_HALF)
        k_z_hi = min(k_ma, k_opt + SURFACE_ZOOM_K_HALF)
        b_z_lo = max(b_mi, b_opt - SURFACE_ZOOM_B_HALF)
        b_z_hi = min(b_ma, b_opt + SURFACE_ZOOM_B_HALF)

        min_span_k = SURFACE_ZOOM_GRID_STEP_K * 4.0
        min_span_b = SURFACE_ZOOM_GRID_STEP_B * 4.0
        if k_z_hi - k_z_lo < min_span_k:
            mid_k = 0.5 * (k_z_lo + k_z_hi)
            k_z_lo = max(k_mi, mid_k - min_span_k / 2.0)
            k_z_hi = min(k_ma, mid_k + min_span_k / 2.0)
        if b_z_hi - b_z_lo < min_span_b:
            mid_b = 0.5 * (b_z_lo + b_z_hi)
            b_z_lo = max(b_mi, mid_b - min_span_b / 2.0)
            b_z_hi = min(b_ma, mid_b + min_span_b / 2.0)

        condition_zoom = condition_surface.copy()
        condition_zoom.k_min = k_z_lo
        condition_zoom.k_max = k_z_hi
        condition_zoom.b_min = b_z_lo
        condition_zoom.b_max = b_z_hi

        Kz, Bz, Zz = self._grid_optimizer.evaluate_surface(
            objective_function=objective,
            condition=condition_zoom,
            grid_step_k=SURFACE_ZOOM_GRID_STEP_K,
            grid_step_b=SURFACE_ZOOM_GRID_STEP_B,
        )

        result: CalculationResult = self._build_result(
            cable=cable,
            k=k_opt,
            b=b_opt,
            mse=mse_min,
            use_mask=use_mask,
        )

        return result, K, B, Z, Kz, Bz, Zz

    def _build_objective(
        self,
        cable: CableRecord,
        use_mask: list[bool],
        condition: SearchCondition,
    ) -> Callable[[float, float], float]:
        """
        CableRecord 等を束縛した objective(k, b) を生成する。

        Args:
            cable:
                ケーブルデータ。
            use_mask:
                使用モードフラグ。
            condition:
                探索条件。

        Returns:
            Callable[[float, float], float]:
                k, b を受けて MSE を返す関数。
        """

        def _objective(k: float, b: float) -> float:
            return objective_function(
                cable=cable,
                k=k,
                b=b,
                use_mask=use_mask,
                condition=condition,
            )

        return _objective

    def _build_result(
        self,
        cable: CableRecord,
        k: float,
        b: float,
        mse: float,
        use_mask: list[bool],
    ) -> CalculationResult:
        """
        最適化で得られた k, b, mse から CalculationResult を生成する。

        Args:
            cable:
                ケーブルデータ。
            k:
                最適張力係数。
            b:
                最適剛性係数。
            mse:
                最小 MSE。
            use_mask:
                使用モードフラグ。

        Returns:
            CalculationResult:
                計算結果。
        """
        tension_kN: float = cable.design_tension_kN * k
        rigidity_Nm2: float = cable.design_rigidity_Nm2 * b  # type: ignore[operator]

        theoretical_frequencies_hz: list[float] = FrequencyFormula.calculate(
            tension_kN=tension_kN,
            rigidity_Nm2=rigidity_Nm2,
            unit_weight_kg_per_m=cable.unit_weight_kg_per_m,
            cable_length_m=cable.cable_length_m,
            max_mode=cable.max_mode,
        )

        xi: float | None = cable.xi

        return CalculationResult(
            k=k,
            b=b,
            tension_kN=tension_kN,
            rigidity_Nm2=rigidity_Nm2,
            xi=xi,
            mse=mse,
            measured_frequencies_hz=cable.measured_frequencies_hz,
            theoretical_frequencies_hz=theoretical_frequencies_hz,
            use_mask=use_mask,
            max_mode=cable.max_mode,
        )