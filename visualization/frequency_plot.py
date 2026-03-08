from typing import Optional

import plotly.graph_objects as go


def create_frequency_plot(
    measured_frequencies_hz: list[Optional[float]],
    theoretical_frequencies_hz: list[float],
    use_mask: list[bool],
) -> go.Figure:
    """
    実測周波数と理論周波数をモード次数ごとに比較するグラフを生成する。

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

    measured_x: list[int] = []
    measured_y: list[float] = []
    measured_text: list[str] = []

    ignored_x: list[int] = []
    ignored_y: list[float] = []
    ignored_text: list[str] = []

    for mode_number, f_obs, use in zip(mode_numbers, measured_frequencies_hz, use_mask):
        if f_obs is None:
            continue

        if use:
            measured_x.append(mode_number)
            measured_y.append(float(f_obs))
            measured_text.append(f"{mode_number}次: {float(f_obs):.4f} Hz")
        else:
            ignored_x.append(mode_number)
            ignored_y.append(float(f_obs))
            ignored_text.append(f"{mode_number}次: {float(f_obs):.4f} Hz (not used)")

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=mode_numbers,
            y=theoretical_frequencies_hz,
            mode="lines+markers",
            name="理論周波数",
            hovertemplate="mode=%{x}<br>theory=%{y:.4f} Hz<extra></extra>",
        )
    )

    fig.add_trace(
        go.Scatter(
            x=measured_x,
            y=measured_y,
            mode="markers",
            name="実測周波数（使用）",
            text=measured_text,
            hovertemplate="%{text}<extra></extra>",
        )
    )

    if ignored_x:
        fig.add_trace(
            go.Scatter(
                x=ignored_x,
                y=ignored_y,
                mode="markers",
                name="実測周波数（未使用）",
                text=ignored_text,
                hovertemplate="%{text}<extra></extra>",
            )
        )

    fig.update_layout(
        title="Mode vs Frequency",
        xaxis_title="モード次数",
        yaxis_title="周波数 [Hz]",
        xaxis=dict(dtick=1),
    )

    return fig