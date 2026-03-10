from typing import Optional

import plotly.graph_objects as go


def create_residual_plot(
    measured_frequencies_hz: list[Optional[float]],
    theoretical_frequencies_hz: list[float],
    use_mask: list[bool],
) -> go.Figure:
    """
    実測周波数と理論周波数の残差グラフを生成する。

    残差は
        residual = f_obs - f_theory
    と定義する。

    Args:
        measured_frequencies_hz:
            実測周波数列 [Hz]。未検出モードは None を許容する。
        theoretical_frequencies_hz:
            理論周波数列 [Hz]。
        use_mask:
            各モードを使用対象とするかどうかのフラグ列。

    Returns:
        go.Figure:
            Plotly Figure オブジェクト。

    Raises:
        ValueError:
            入力列長が一致しない場合。
    """
    if not (
        len(measured_frequencies_hz)
        == len(theoretical_frequencies_hz)
        == len(use_mask)
    ):
        raise ValueError(
            "Input lengths must match: measured_frequencies_hz, "
            "theoretical_frequencies_hz, use_mask."
        )

    mode_numbers: list[int] = list(range(1, len(theoretical_frequencies_hz) + 1))

    used_x: list[int] = []
    used_y: list[float] = []
    used_text: list[str] = []

    ignored_x: list[int] = []
    ignored_y: list[float] = []
    ignored_text: list[str] = []

    for mode_number, f_obs, f_theory, use in zip(
        mode_numbers,
        measured_frequencies_hz,
        theoretical_frequencies_hz,
        use_mask,
    ):
        if f_obs is None:
            continue

        residual: float = float(f_obs) - float(f_theory)
        text: str = (
            f"{mode_number}次"
            f"<br>obs={float(f_obs):.4f} Hz"
            f"<br>theory={float(f_theory):.4f} Hz"
            f"<br>residual={residual:.4f} Hz"
        )

        if use:
            used_x.append(mode_number)
            used_y.append(residual)
            used_text.append(text)
        else:
            ignored_x.append(mode_number)
            ignored_y.append(residual)
            ignored_text.append(text + "<br>(not used)")

    fig = go.Figure()

    fig.add_hline(y=0.0)

    fig.add_trace(
        go.Scatter(
            x=used_x,
            y=used_y,
            mode="markers+lines",
            name="残差（使用）",
            text=used_text,
            hovertemplate="%{text}<extra></extra>",
        )
    )

    if ignored_x:
        fig.add_trace(
            go.Scatter(
                x=ignored_x,
                y=ignored_y,
                mode="markers",
                name="残差（未使用）",
                text=ignored_text,
                hovertemplate="%{text}<extra></extra>",
            )
        )

    fig.update_layout(
        title="Residual Plot",
        xaxis_title="モード次数",
        yaxis_title="残差 [Hz] (実測 - 理論)",
        xaxis=dict(dtick=1),
        yaxis=dict(range=[-1, 1]),
    )

    return fig