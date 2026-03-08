import math


class XiCalculator:
    """
    ケーブルの ξ パラメータを計算するクラス。
    ξ は結果評価・整理用の指標として扱う。
    """

    @staticmethod
    def calculate(
        cable_length_m: float,
        tension_kN: float,
        rigidity_Nm2: float,
    ) -> float:
        """
        ξ を計算する。

        Args:
            cable_length_m: ケーブル長 [m]
            tension_kN: 張力 [kN]
            rigidity_Nm2: 曲げ剛性 [N·m^2]

        Returns:
            ξ [-]
        """
        if cable_length_m <= 0:
            raise ValueError("cable_length_m must be positive.")

        if tension_kN <= 0:
            raise ValueError("tension_kN must be positive.")

        if rigidity_Nm2 <= 0:
            raise ValueError("rigidity_Nm2 must be positive.")

        tension_N = tension_kN * 1000.0
        return cable_length_m * math.sqrt(tension_N / rigidity_Nm2)