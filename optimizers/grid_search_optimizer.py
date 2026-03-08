import numpy as np

from domain.models.search_condition import SearchCondition


class GridSearchOptimizer:
    """
    グリッドサーチにより目的関数の最小値を探索する optimizer。

    探索対象は 2変数 (k, b) とし、SearchCondition に定義された
    範囲と刻み幅に基づいて総当たり評価を行う。
    """

    def optimize(
        self,
        objective_function,
        condition: SearchCondition,
    ) -> tuple[float, float, float]:
        """
        グリッドサーチを実行し、最小となる k, b, objective 値を返す。

        Args:
            objective_function:
                2変数 (k, b) を受け取り、スカラー値（MSE）を返す関数。
            condition:
                探索条件。

        Returns:
            tuple[float, float, float]:
                (k_opt, b_opt, objective_min)

        Raises:
            ValueError:
                有効な探索点が存在しない場合。
        """
        K, B, Z = self.evaluate_surface(
            objective_function=objective_function,
            condition=condition,
        )

        valid_mask: np.ndarray = np.isfinite(Z)
        if not np.any(valid_mask):
            raise ValueError("No valid grid points found.")

        flat_index: int = int(np.argmin(Z[valid_mask]))
        k_opt: float = float(K[valid_mask].ravel()[flat_index])
        b_opt: float = float(B[valid_mask].ravel()[flat_index])
        objective_min: float = float(Z[valid_mask].ravel()[flat_index])

        return k_opt, b_opt, objective_min

    def evaluate_surface(
        self,
        objective_function,
        condition: SearchCondition,
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        指定された探索範囲で目的関数をグリッド評価し、3D表示用の
        K, B, Z を返す。

        Args:
            objective_function:
                2変数 (k, b) を受け取り、スカラー値（MSE）を返す関数。
            condition:
                探索条件。

        Returns:
            tuple[np.ndarray, np.ndarray, np.ndarray]:
                - K: k の meshgrid
                - B: b の meshgrid
                - Z: 各格子点の objective 値

        Raises:
            ValueError:
                刻み幅が0以下の場合。
                探索範囲が不正な場合。
        """
        self._validate_condition(condition)

        k_values: np.ndarray = np.arange(
            condition.k_min,
            condition.k_max + condition.grid_step_k / 2.0,
            condition.grid_step_k,
            dtype=float,
        )
        b_values: np.ndarray = np.arange(
            condition.b_min,
            condition.b_max + condition.grid_step_b / 2.0,
            condition.grid_step_b,
            dtype=float,
        )

        K, B = np.meshgrid(k_values, b_values)
        Z: np.ndarray = np.empty_like(K, dtype=float)

        for row_index in range(B.shape[0]):
            for col_index in range(K.shape[1]):
                k: float = float(K[row_index, col_index])
                b: float = float(B[row_index, col_index])

                try:
                    z_value = objective_function(k, b)
                    Z[row_index, col_index] = float(z_value)
                except (ValueError, ZeroDivisionError, OverflowError, FloatingPointError):
                    Z[row_index, col_index] = np.inf

        return K, B, Z

    @staticmethod
    def _validate_condition(condition: SearchCondition) -> None:
        """
        グリッドサーチ条件の妥当性を確認する。

        Args:
            condition:
                探索条件。

        Raises:
            ValueError:
                条件が不正な場合。
        """
        if condition.grid_step_k <= 0:
            raise ValueError("grid_step_k must be positive.")
        if condition.grid_step_b <= 0:
            raise ValueError("grid_step_b must be positive.")

        if condition.k_min > condition.k_max:
            raise ValueError("k_min must be less than or equal to k_max.")
        if condition.b_min > condition.b_max:
            raise ValueError("b_min must be less than or equal to b_max.")