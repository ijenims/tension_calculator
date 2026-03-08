from domain.evaluation.objective_function import objective_function
from domain.models.calculation_result import CalculationResult
from domain.models.cable_record import CableRecord
from domain.models.search_condition import SearchCondition
from domain.physics.frequency_formula import FrequencyFormula
from domain.physics.xi_calculator import XiCalculator


class ManualFrequencyService:
    """
    手動入力された k, b を用いて理論周波数・MSE・ξ を計算するサービス。

    本サービスは探索を行わず、与えられた k, b をそのまま採用して
    CalculationResult を生成する。
    """

    def calculate(
        self,
        cable: CableRecord,
        k: float,
        b: float,
        use_mask: list[bool],
        condition: SearchCondition,
    ) -> CalculationResult:
        """
        手動入力の k, b に基づいて計算結果を生成する。

        Args:
            cable:
                ケーブル諸元および実測周波数を保持するデータ。
            k:
                設計張力に対する係数。
            b:
                設計剛性に対する係数。
            use_mask:
                各モードを比較対象に含めるかどうかのフラグ列。
            condition:
                MSE評価条件。weight_mode や use_normalized_mse を使用する。

        Returns:
            CalculationResult:
                手動計算結果。

        Raises:
            ValueError:
                設計剛性が未設定の場合。
                use_mask 長が max_mode と一致しない場合。
                理論周波数計算が成立しない場合。
        """
        if cable.design_rigidity_Nm2 is None:
            raise ValueError("design_rigidity_Nm2 is required for manual calculation.")

        if len(use_mask) != cable.max_mode:
            raise ValueError("use_mask length must match cable.max_mode.")

        tension_kN: float = cable.design_tension_kN * k
        rigidity_Nm2: float = cable.design_rigidity_Nm2 * b

        theoretical_frequencies_hz: list[float] = FrequencyFormula.calculate(
            tension_kN=tension_kN,
            rigidity_Nm2=rigidity_Nm2,
            unit_weight_kg_per_m=cable.unit_weight_kg_per_m,
            cable_length_m=cable.cable_length_m,
            max_mode=cable.max_mode,
        )

        mse: float = objective_function(
            cable=cable,
            k=k,
            b=b,
            use_mask=use_mask,
            condition=condition,
        )

        if mse == float("inf"):
            raise ValueError("Manual calculation resulted in an invalid objective value.")

        xi: float = XiCalculator.calculate(
            cable_length_m=cable.cable_length_m,
            tension_kN=tension_kN,
            rigidity_Nm2=rigidity_Nm2,
        )

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