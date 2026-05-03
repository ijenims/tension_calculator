import numpy as np

from config.grid_multistage import (
    BOUNDARY_MARGIN_B,
    BOUNDARY_MARGIN_K,
    BOUNDARY_MARGIN_MAX_FRACTION_OF_SPAN,
    COARSE_GRID_STEP_B,
    COARSE_GRID_STEP_K,
    EXPAND_B,
    EXPAND_K,
    FINE_B_HALF_WIDTH,
    FINE_GRID_STEP_B,
    FINE_GRID_STEP_K,
    FINE_K_HALF_WIDTH,
    MAX_RANGE_EXPANSION_ROUNDS,
    MEDIUM_B_HALF_WIDTH,
    MEDIUM_GRID_STEP_B,
    MEDIUM_GRID_STEP_K,
    MEDIUM_K_HALF_WIDTH,
    MULTISTAGE_TOP_N,
)
from domain.models.search_condition import SearchCondition


def _kb_key(k: float, b: float) -> tuple[float, float]:
    return (round(float(k), 10), round(float(b), 10))


class GridSearchOptimizer:
    """
    グリッドサーチにより目的関数の最小値を探索する optimizer。

    grid 手法では粗→中→細の多段探索を行う。
    単一の等間隔全域グリッドは 3D 表示用 evaluate_surface のみで使用する。
    """

    def __init__(self) -> None:
        self._last_search_bounds: tuple[float, float, float, float] | None = None

    @property
    def last_search_bounds(self) -> tuple[float, float, float, float]:
        """
        直近の optimize 完了後の探索枠 (k_min, k_max, b_min, b_max)。
        範囲拡張が入った場合は拡張後の値。
        """
        if self._last_search_bounds is None:
            raise RuntimeError("optimize() has not been run yet.")
        return self._last_search_bounds

    def optimize(
        self,
        objective_function,
        condition: SearchCondition,
    ) -> tuple[float, float, float]:
        """
        多段グリッドサーチを実行し、最小となる k, b, objective 値を返す。
        """
        k_opt, b_opt, z_opt, bounds = self._optimize_multistage_core(
            objective_function=objective_function,
            condition=condition,
        )
        self._last_search_bounds = bounds
        return k_opt, b_opt, z_opt

    def _optimize_multistage_core(
        self,
        objective_function,
        condition: SearchCondition,
    ) -> tuple[float, float, float, tuple[float, float, float, float]]:
        self._validate_condition(condition)

        cache: dict[tuple[float, float], float] = {}

        def eval_point(k: float, b: float) -> float:
            key = _kb_key(k, b)
            if key in cache:
                return cache[key]
            try:
                z_value = float(objective_function(k, b))
            except (ValueError, ZeroDivisionError, OverflowError, FloatingPointError):
                z_value = float(np.inf)
            cache[key] = z_value
            return z_value

        k_min, k_max = float(condition.k_min), float(condition.k_max)
        b_min, b_max = float(condition.b_min), float(condition.b_max)

        best_k: float = float(k_min)
        best_b: float = float(b_min)
        best_z: float = float(np.inf)

        def update_best(k: float, b: float) -> None:
            nonlocal best_k, best_b, best_z
            z = eval_point(k, b)
            if z < best_z:
                best_k, best_b, best_z = k, b, z

        for _ in range(MAX_RANGE_EXPANSION_ROUNDS):
            # ----- 粗 -----
            coarse_points = self._iter_grid_points(
                k_min, k_max, COARSE_GRID_STEP_K,
                b_min, b_max, COARSE_GRID_STEP_B,
            )
            for k, b in coarse_points:
                update_best(k, b)

            top_coarse = self._top_n_from_points(coarse_points, cache, MULTISTAGE_TOP_N)

            # ----- 中 -----
            med_points: list[tuple[float, float]] = []
            for kc, bc, _z in top_coarse:
                med_points.extend(
                    self._iter_grid_points(
                        max(k_min, kc - MEDIUM_K_HALF_WIDTH),
                        min(k_max, kc + MEDIUM_K_HALF_WIDTH),
                        MEDIUM_GRID_STEP_K,
                        max(b_min, bc - MEDIUM_B_HALF_WIDTH),
                        min(b_max, bc + MEDIUM_B_HALF_WIDTH),
                        MEDIUM_GRID_STEP_B,
                    )
                )
            for k, b in med_points:
                update_best(k, b)

            top_med = self._top_n_from_points(med_points, cache, MULTISTAGE_TOP_N)

            # ----- 細 -----
            fine_points: list[tuple[float, float]] = []
            for kc, bc, _z in top_med:
                fine_points.extend(
                    self._iter_grid_points(
                        max(k_min, kc - FINE_K_HALF_WIDTH),
                        min(k_max, kc + FINE_K_HALF_WIDTH),
                        FINE_GRID_STEP_K,
                        max(b_min, bc - FINE_B_HALF_WIDTH),
                        min(b_max, bc + FINE_B_HALF_WIDTH),
                        FINE_GRID_STEP_B,
                    )
                )
            for k, b in fine_points:
                update_best(k, b)

            margin_k = GridSearchOptimizer._effective_edge_margin(
                k_min, k_max, BOUNDARY_MARGIN_K, BOUNDARY_MARGIN_MAX_FRACTION_OF_SPAN
            )
            margin_b = GridSearchOptimizer._effective_edge_margin(
                b_min, b_max, BOUNDARY_MARGIN_B, BOUNDARY_MARGIN_MAX_FRACTION_OF_SPAN
            )

            expanded = False
            if margin_k > 0.0 and best_k <= k_min + margin_k:
                k_min -= EXPAND_K
                expanded = True
            if margin_k > 0.0 and best_k >= k_max - margin_k:
                k_max += EXPAND_K
                expanded = True
            if margin_b > 0.0 and best_b <= b_min + margin_b:
                b_min -= EXPAND_B
                expanded = True
            if margin_b > 0.0 and best_b >= b_max - margin_b:
                b_max += EXPAND_B
                expanded = True

            if not expanded:
                break

        if not np.isfinite(best_z):
            raise ValueError("No valid grid points found.")

        final_bounds = (k_min, k_max, b_min, b_max)
        return best_k, best_b, float(best_z), final_bounds

    @staticmethod
    def _effective_edge_margin(
        lo: float,
        hi: float,
        abs_margin: float,
        max_fraction_of_span: float,
    ) -> float:
        """
        枠の半幅に対して大きすぎる絶対マージンを抑える。

        区間が狭いときに「端」の判定が全域を覆い、ユーザ指定の k/b 範囲が
        毎ラウンド拡張されて打ち消されるのを防ぐ。
        """
        span = float(hi) - float(lo)
        if span <= 0.0:
            return 0.0
        cap = span * float(max_fraction_of_span)
        return float(min(abs_margin, cap))

    @staticmethod
    def _iter_grid_points(
        k_lo: float,
        k_hi: float,
        k_step: float,
        b_lo: float,
        b_hi: float,
        b_step: float,
    ) -> list[tuple[float, float]]:
        if k_lo > k_hi or b_lo > b_hi or k_step <= 0 or b_step <= 0:
            return []
        k_vals = np.arange(
            k_lo,
            k_hi + k_step / 2.0,
            k_step,
            dtype=float,
        )
        b_vals = np.arange(
            b_lo,
            b_hi + b_step / 2.0,
            b_step,
            dtype=float,
        )
        points: list[tuple[float, float]] = []
        for b in b_vals:
            for k in k_vals:
                points.append((float(k), float(b)))
        return points

    @staticmethod
    def _top_n_from_points(
        points: list[tuple[float, float]],
        cache: dict[tuple[float, float], float],
        n: int,
    ) -> list[tuple[float, float, float]]:
        scored: list[tuple[float, float, float]] = []
        seen: set[tuple[float, float]] = set()
        for k, b in points:
            key = _kb_key(k, b)
            if key in seen:
                continue
            seen.add(key)
            z = cache.get(key, float(np.inf))
            scored.append((k, b, z))
        scored.sort(key=lambda t: t[2])
        return scored[:n]

    def evaluate_surface(
        self,
        objective_function,
        condition: SearchCondition,
        grid_step_k: float | None = None,
        grid_step_b: float | None = None,
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        指定された探索範囲で目的関数をグリッド評価し、3D表示用の K, B, Z を返す。

        grid_step_k / grid_step_b を省略した場合は condition の刻みを使用する。
        """
        self._validate_condition(condition)

        gk = float(condition.grid_step_k) if grid_step_k is None else float(grid_step_k)
        gb = float(condition.grid_step_b) if grid_step_b is None else float(grid_step_b)
        if gk <= 0 or gb <= 0:
            raise ValueError("grid steps must be positive.")

        k_values: np.ndarray = np.arange(
            condition.k_min,
            condition.k_max + gk / 2.0,
            gk,
            dtype=float,
        )
        b_values: np.ndarray = np.arange(
            condition.b_min,
            condition.b_max + gb / 2.0,
            gb,
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
        if condition.grid_step_k <= 0:
            raise ValueError("grid_step_k must be positive.")
        if condition.grid_step_b <= 0:
            raise ValueError("grid_step_b must be positive.")

        if condition.k_min > condition.k_max:
            raise ValueError("k_min must be less than or equal to k_max.")
        if condition.b_min > condition.b_max:
            raise ValueError("b_min must be less than or equal to b_max.")
