import numpy as np
from scipy.optimize import minimize

from domain.models.search_condition import SearchCondition


class ScipyOptimizer:
    """
    scipy.optimize を利用して目的関数の最小値を探索する optimizer。

    探索対象は (k, b) の2変数。
    """

    def optimize(
        self,
        objective_function,
        condition: SearchCondition,
    ) -> tuple[float, float, float]:
        """
        scipy.optimize.minimize により最適解を探索する。

        Args:
            objective_function:
                (k, b) を入力とし MSE を返す関数
            condition:
                探索条件

        Returns
        -------
        tuple
            (k_opt, b_opt, mse_min)

        Raises
        ------
        ValueError
            最適化に失敗した場合
        """

        initial_k: float = (condition.k_min + condition.k_max) / 2.0
        initial_b: float = (condition.b_min + condition.b_max) / 2.0

        bounds = [
            (condition.k_min, condition.k_max),
            (condition.b_min, condition.b_max),
        ]

        def _objective(x: np.ndarray) -> float:
            k = float(x[0])
            b = float(x[1])
            return objective_function(k, b)

        result = minimize(
            fun=_objective,
            x0=np.array([initial_k, initial_b], dtype=float),
            bounds=bounds,
            method="L-BFGS-B",
        )

        if not result.success:
            raise ValueError(f"Optimization failed: {result.message}")

        k_opt: float = float(result.x[0])
        b_opt: float = float(result.x[1])
        mse_min: float = float(result.fun)

        return k_opt, b_opt, mse_min