from dataclasses import dataclass
from typing import Optional


@dataclass
class SearchCondition:
    """
    張力・剛性推定における探索条件を保持するデータクラス。

    Attributes
    ----------
    method:
        探索アルゴリズム。
        例: "grid", "scipy"

    k_min, k_max:
        張力係数 k の探索範囲。

    b_min, b_max:
        剛性係数 b の探索範囲。

    grid_step_k:
        グリッドサーチ時の k 刻み幅。

    grid_step_b:
        グリッドサーチ時の b 刻み幅。

    weight_mode:
        誤差評価時の重み付け方式。
        - "none":
            重みなし（全て1.0）
        - "mode_number":
            実モード番号をそのまま重みとして使用
            例: mode=[1,3,5] → weight=[1,3,5]
        - "manual":
            manual_weights を使用

    manual_weights:
        手動指定の重み列。
        weight_mode="manual" の場合のみ使用する。

    use_normalized_mse:
        True の場合、相対誤差ベースの MSE を使用。
        False の場合、絶対誤差ベースの MSE を使用。
    """

    method: str

    k_min: float
    k_max: float
    b_min: float
    b_max: float

    grid_step_k: float
    grid_step_b: float

    weight_mode: str
    manual_weights: Optional[list[float]] = None

    use_normalized_mse: bool = False