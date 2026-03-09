import math


class DesignRigidityCalculator:
    """
    単位重量から設計曲げ剛性を推定するクラス。
    主用途は、設計剛性がDBに存在しない場合の補完計算。
    """

    DENSITY_G_CM3: float = 7.85
    RHO_KG_M3: float = DENSITY_G_CM3 * 1000.0
    YOUNGS_MODULUS_N_M2: float = 196_000 * 10**6

    @classmethod
    def calculate_theoretical_diameter_m(
        cls,
        unit_weight_kg_per_m: float,
    ) -> float:
        """
        単位重量から理論ケーブル径を計算する。

        Args:
            unit_weight_kg_per_m: 単位重量 [kg/m]

        Returns:
            理論ケーブル径 [m]
        """
        if unit_weight_kg_per_m <= 0:
            raise ValueError("unit_weight_kg_per_m must be positive.")

        return math.sqrt(unit_weight_kg_per_m * 4.0 / (cls.RHO_KG_M3 * math.pi))

    @staticmethod
    def calculate_moment_of_inertia_m4(
        diameter_m: float,
    ) -> float:
        """
        円断面の断面二次モーメントを計算する。

        Args:
            diameter_m: 直径 [m]

        Returns:
            断面二次モーメント [m^4]
        """
        if diameter_m <= 0:
            raise ValueError("diameter_m must be positive.")

        return math.pi * diameter_m**4 / 64.0

    @classmethod
    def calculate_from_unit_weight(
        cls,
        unit_weight_kg_per_m: float,
    ) -> float:
        """
        単位重量から設計曲げ剛性を計算する。

        Args:
            unit_weight_kg_per_m: 単位重量 [kg/m]

        Returns:
            設計曲げ剛性 [N·m^2]
        """
        diameter_m = cls.calculate_theoretical_diameter_m(unit_weight_kg_per_m)
        moment_of_inertia_m4 = cls.calculate_moment_of_inertia_m4(diameter_m)
        return cls.YOUNGS_MODULUS_N_M2 * moment_of_inertia_m4

    @classmethod
    def apply_beta(
        cls,
        design_rigidity_Nm2: float,
        beta: float,
    ) -> float:
        """
        設計曲げ剛性に補正係数を掛ける。

        Args:
            design_rigidity_Nm2: 設計曲げ剛性 [N·m^2]
            beta: 補正係数 [-]

        Returns:
            補正後曲げ剛性 [N·m^2]
        """

        return design_rigidity_Nm2 * beta