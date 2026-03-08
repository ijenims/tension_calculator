import math


class FrequencyFormula:
    """
    張力・曲げ剛性・単位重量・ケーブル長から
    1次〜max_mode次の理論固有振動数を計算するクラス。
    """

    @staticmethod
    def calculate(
        tension_kN: float,
        rigidity_Nm2: float,
        unit_weight_kg_per_m: float,
        cable_length_m: float,
        max_mode: int = 7,
    ) -> list[float]:
        """
        Args:
            tension_kN: 張力 [kN]
            rigidity_Nm2: 曲げ剛性 [N·m^2]
            unit_weight_kg_per_m: 単位重量 [kg/m]
            cable_length_m: ケーブル長 [m]
            max_mode: 最大次数（標準7、最大10想定）

        Returns:
            理論固有振動数リスト [Hz]
        """
        if tension_kN == 0:
            raise ValueError("tension_kN must not be zero.")
        if unit_weight_kg_per_m <= 0:
            raise ValueError("unit_weight_kg_per_m must be positive.")
        if cable_length_m <= 0:
            raise ValueError("cable_length_m must be positive.")
        if max_mode <= 0:
            raise ValueError("max_mode must be positive.")

        tension_N = tension_kN * 1000.0
        rho_A = unit_weight_kg_per_m
        L = cable_length_m
        EI = rigidity_Nm2

        frequencies: list[float] = []

        for mode in range(1, max_mode + 1):
            term1 = (math.pi**2 * EI * mode**4) / (4.0 * rho_A * L**4)
            term2 = (tension_N * mode**2) / (4.0 * rho_A * L**2)
            f_squared = term1 + term2

            if f_squared <= 0:
                raise ValueError(
                    f"Invalid frequency square at mode={mode}. "
                    f"tension_kN={tension_kN}, rigidity_Nm2={rigidity_Nm2}"
                )

            frequencies.append(math.sqrt(f_squared))

        return frequencies