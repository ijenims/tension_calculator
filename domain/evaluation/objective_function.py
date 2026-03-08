import numpy as np

from domain.evaluation.mask import apply_mask_with_none
from domain.evaluation.mse import calculate_mse, calculate_normalized_mse
from domain.evaluation.weighting import build_weights, calculate_weighted_mse
from domain.models.cable_record import CableRecord
from domain.models.search_condition import SearchCondition
from domain.physics.frequency_formula import FrequencyFormula


def objective_function(
    cable: CableRecord,
    k: float,
    b: float,
    use_mask: list[bool],
    condition: SearchCondition,
) -> float:
    """
    与えられた k, b に対する目的関数値（MSE）を計算する。

    本関数は、設計張力・設計剛性に対して係数 k, b を掛けた値から
    理論周波数列を生成し、実測周波数列との誤差を MSE として返す。

    Args:
        cable:
            ケーブル諸元および実測周波数を保持するデータ。
        k:
            設計張力に対する係数。
            tension_kN = cable.design_tension_kN * k
        b:
            設計剛性に対する係数。
            rigidity_Nm2 = cable.design_rigidity_Nm2 * b
        use_mask:
            各モードを比較対象に含めるかどうかのフラグ列。
        condition:
            重み付け方式、正規化MSEの有無などの探索条件。

    Returns:
        float:
            目的関数値（MSE）。
            計算不能・不正条件の場合は np.inf を返す。
    """
    try:
        if cable.design_rigidity_Nm2 is None:
            return np.inf

        if len(use_mask) != cable.max_mode:
            return np.inf

        tension_kN: float = cable.design_tension_kN * k
        rigidity_Nm2: float = cable.design_rigidity_Nm2 * b

        theoretical_frequencies_hz: list[float] = FrequencyFormula.calculate(
            tension_kN=tension_kN,
            rigidity_Nm2=rigidity_Nm2,
            unit_weight_kg_per_m=cable.unit_weight_kg_per_m,
            cable_length_m=cable.cable_length_m,
            max_mode=cable.max_mode,
        )

        measured_used, theoretical_used, mode_numbers = apply_mask_with_none(
            measured_frequencies_hz=cable.measured_frequencies_hz,
            theoretical_frequencies_hz=theoretical_frequencies_hz,
            use_mask=use_mask,
        )

        if condition.weight_mode == "none":
            if condition.use_normalized_mse:
                return calculate_normalized_mse(
                    sequence1=measured_used,
                    sequence2=theoretical_used,
                )
            return calculate_mse(
                sequence1=measured_used,
                sequence2=theoretical_used,
            )

        weights: list[float] = build_weights(
            weight_mode=condition.weight_mode,
            mode_numbers=mode_numbers,
            manual_weights=condition.manual_weights,
        )

        return calculate_weighted_mse(
            sequence1=measured_used,
            sequence2=theoretical_used,
            weights=weights,
            normalized=condition.use_normalized_mse,
        )

    except (ValueError, ZeroDivisionError, OverflowError, FloatingPointError):
        return np.inf