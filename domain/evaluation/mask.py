from typing import Optional


def apply_mask_with_none(
    measured_frequencies_hz: list[Optional[float]],
    theoretical_frequencies_hz: list[float],
    use_mask: list[bool],
) -> tuple[list[float], list[float], list[int]]:
    """
    実測周波数列・理論周波数列に対して、None除外と use_mask による
    共通フィルタリングを適用する。

    比較対象として有効なデータのみを抽出し、あわせて実モード番号
    （1始まり）も返す。

    Args:
        measured_frequencies_hz:
            実測周波数列 [Hz]。未検出モードは None を許容する。
        theoretical_frequencies_hz:
            理論周波数列 [Hz]。
        use_mask:
            各モードを比較対象に含めるかどうかのフラグ列。

    Returns:
        tuple[list[float], list[float], list[int]]:
            - フィルタ後の実測周波数列
            - フィルタ後の理論周波数列
            - フィルタ後の実モード番号列（1始まり）

    Raises:
        ValueError:
            入力リスト長が一致しない場合。
            または、比較対象となる有効データが1件もない場合。
    """
    if not (
        len(measured_frequencies_hz)
        == len(theoretical_frequencies_hz)
        == len(use_mask)
    ):
        raise ValueError(
            "Input lengths must match: "
            "measured_frequencies_hz, theoretical_frequencies_hz, use_mask."
        )

    measured_used: list[float] = []
    theoretical_used: list[float] = []
    mode_numbers: list[int] = []

    for mode_number, (f_obs, f_theory, use) in enumerate(
        zip(measured_frequencies_hz, theoretical_frequencies_hz, use_mask),
        start=1,
    ):
        if (f_obs is not None) and use:
            measured_used.append(float(f_obs))
            theoretical_used.append(float(f_theory))
            mode_numbers.append(mode_number)

    if len(measured_used) == 0:
        raise ValueError("No valid frequencies selected for comparison.")

    return measured_used, theoretical_used, mode_numbers