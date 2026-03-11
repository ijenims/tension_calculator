from dataclasses import dataclass
from typing import Optional

from config.defaults import (
    DEFAULT_B_MAX,
    DEFAULT_B_MIN,
    DEFAULT_GRID_STEP_B,
    DEFAULT_GRID_STEP_K,
    DEFAULT_K_MAX,
    DEFAULT_K_MIN,
    DEFAULT_METHOD,
    DEFAULT_USE_NORMALIZED_MSE,
    DEFAULT_WEIGHT_MODE,
)


@dataclass
class SearchCondition:
    """
    張力・剛性推定における探索条件を保持する業務状態オブジェクト。

    このクラスは、最適化に必要な探索条件をひとまとめに保持する。
    Streamlit の widget state とは切り離して扱い、
    「業務上の意味を持つ探索条件の唯一の保持先」とする。

    Attributes:
        method:
            探索アルゴリズム。
            想定値は "grid" または "scipy"。
        k_min:
            張力係数 k の探索下限。
        k_max:
            張力係数 k の探索上限。
        b_min:
            剛性係数 b の探索下限。
        b_max:
            剛性係数 b の探索上限。
        grid_step_k:
            grid 探索時の k 刻み幅。
        grid_step_b:
            grid 探索時の b 刻み幅。
        weight_mode:
            誤差評価時の重み付け方式。
            - "none": 重みなし
            - "mode_number": モード次数を重みとして使用
            - "manual": manual_weights を使用
        manual_weights:
            手動指定の重み列。
            weight_mode="manual" の場合のみ使用する。
        use_normalized_mse:
            True の場合、相対誤差ベースの MSE を使用する。
            False の場合、絶対誤差ベースの MSE を使用する。
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

    @classmethod
    def default(cls) -> "SearchCondition":
        """
        デフォルト探索条件を生成する。

        case_key（facility, cable, branch）が変わったときは、
        このメソッドで新しい SearchCondition を作り直すことを想定する。

        Returns:
            SearchCondition:
                defaults.py に定義された既定値を持つ探索条件。
        """
        return cls(
            method=DEFAULT_METHOD,
            k_min=float(DEFAULT_K_MIN),
            k_max=float(DEFAULT_K_MAX),
            b_min=float(DEFAULT_B_MIN),
            b_max=float(DEFAULT_B_MAX),
            grid_step_k=float(DEFAULT_GRID_STEP_K),
            grid_step_b=float(DEFAULT_GRID_STEP_B),
            weight_mode=DEFAULT_WEIGHT_MODE,
            manual_weights=None,
            use_normalized_mse=bool(DEFAULT_USE_NORMALIZED_MSE),
        )

    def copy(self) -> "SearchCondition":
        """
        現在の探索条件の複製を返す。

        Streamlit UI から一時的に値を受け取り、
        既存状態を壊さず比較・更新したい場合に使える。

        Returns:
            SearchCondition:
                同じ値を持つ新しいインスタンス。
        """
        manual_weights_copy = None
        if self.manual_weights is not None:
            manual_weights_copy = list(self.manual_weights)

        return SearchCondition(
            method=self.method,
            k_min=self.k_min,
            k_max=self.k_max,
            b_min=self.b_min,
            b_max=self.b_max,
            grid_step_k=self.grid_step_k,
            grid_step_b=self.grid_step_b,
            weight_mode=self.weight_mode,
            manual_weights=manual_weights_copy,
            use_normalized_mse=self.use_normalized_mse,
        )