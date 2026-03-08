import numpy as np


def build_weights(
    weight_mode: str,
    mode_numbers: list[int],
    manual_weights: list[float] | None = None,
) -> list[float]:
    """
    重み設定に応じて、比較対象モードに対応する重み列を生成する。

    Args:
        weight_mode:
            重み付け方式。
            - "none": 重みなし（全て1.0）
            - "mode_number": 実モード番号をそのまま重みに使う
            - "manual": manual_weights を使う
        mode_numbers:
            比較対象として採用された実モード番号列（1始まり）。
            例: [1, 3, 5]
        manual_weights:
            手動指定の重み列。weight_mode="manual" のときのみ使用する。

    Returns:
        list[float]:
            各比較対象データに対応する重み列。

    Raises:
        ValueError:
            mode_numbers が空の場合。
            weight_mode が不正な場合。
            manual_weights の長さが mode_numbers と一致しない場合。
    """
    if len(mode_numbers) == 0:
        raise ValueError("mode_numbers must not be empty.")

    if weight_mode == "none":
        return [1.0] * len(mode_numbers)

    if weight_mode == "mode_number":
        return [float(mode_number) for mode_number in mode_numbers]

    if weight_mode == "manual":
        if manual_weights is None:
            raise ValueError("manual_weights is required when weight_mode='manual'.")
        if len(manual_weights) != len(mode_numbers):
            raise ValueError(
                "manual_weights length must match mode_numbers length."
            )
        return [float(weight) for weight in manual_weights]

    raise ValueError(f"Unknown weight_mode: {weight_mode}")


def calculate_weighted_mse(
    sequence1: list[float],
    sequence2: list[float],
    weights: list[float],
    normalized: bool = False,
) -> float:
    """
    重み付きMSEを計算する。

    Args:
        sequence1:
            比較対象の第1系列。
        sequence2:
            比較対象の第2系列。
        weights:
            各要素に対応する重み列。
        normalized:
            True の場合、相対誤差ベースの重み付きMSEを計算する。
            False の場合、絶対誤差ベースの重み付きMSEを計算する。

    Returns:
        float:
            重み付きMSE。

    Raises:
        ValueError:
            入力配列長が一致しない場合。
            入力列が空の場合。
            重みが負を含む場合。
            重み和が0の場合。
            normalized=True かつ sequence2 に0が含まれる場合。
    """
    if not (len(sequence1) == len(sequence2) == len(weights)):
        raise ValueError("Input lengths must match.")
    if len(sequence1) == 0:
        raise ValueError("Input sequences must not be empty.")

    x1 = np.asarray(sequence1, dtype=float)
    x2 = np.asarray(sequence2, dtype=float)
    w = np.asarray(weights, dtype=float)

    if np.any(w < 0):
        raise ValueError("weights must be non-negative.")
    if np.sum(w) == 0:
        raise ValueError("weights sum must be positive.")

    if normalized:
        if np.any(x2 == 0):
            raise ValueError(
                "sequence2 contains zero; normalized weighted MSE is undefined."
            )
        error = (x1 - x2) / x2
    else:
        error = x1 - x2

    return float(np.sum(w * (error ** 2)) / np.sum(w))