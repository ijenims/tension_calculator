from dataclasses import dataclass
from typing import Optional

import pandas as pd
import streamlit as st


@dataclass
class FrequencyEditorState:
    """
    周波数編集テーブルの状態を保持するデータクラス。
    """

    measured_frequencies_hz: list[Optional[float]]
    use_mask: list[bool]


def render_frequency_editor(
    measured_frequencies_hz: list[Optional[float]],
    use_mask: list[bool],
    theoretical_frequencies_hz: list[float],
    max_mode: int,
) -> FrequencyEditorState:
    """
    周波数編集テーブルを描画し、編集後の実測周波数列と use_mask を返す。

    表の構成は以下。
        行: 実測周波数 / 使用 / 理論周波数
        列: 1次, 2次, ..., max_mode次

    Args:
        measured_frequencies_hz:
            実測周波数列 [Hz]。未検出は None を許容する。
        use_mask:
            各モードの使用フラグ列。
        theoretical_frequencies_hz:
            理論周波数列 [Hz]。
        max_mode:
            最大モード次数。

    Returns:
        FrequencyEditorState:
            編集後の状態。

    Raises:
        ValueError:
            入力列長が max_mode と一致しない場合。
    """
    if len(measured_frequencies_hz) != max_mode:
        raise ValueError("measured_frequencies_hz length must match max_mode.")
    if len(use_mask) != max_mode:
        raise ValueError("use_mask length must match max_mode.")
    if len(theoretical_frequencies_hz) != max_mode:
        raise ValueError("theoretical_frequencies_hz length must match max_mode.")

    st.subheader("周波数編集")

    editor_df: pd.DataFrame = build_frequency_editor_dataframe(
        measured_frequencies_hz=measured_frequencies_hz,
        use_mask=use_mask,
        theoretical_frequencies_hz=theoretical_frequencies_hz,
        max_mode=max_mode,
    )

    edited_df: pd.DataFrame = st.data_editor(
        editor_df,
        use_container_width=True,
        hide_index=False,
        disabled=["理論周波数 [Hz]"],
        key="frequency_editor_table",
    )

    edited_measured_frequencies_hz, edited_use_mask = parse_frequency_editor_dataframe(
        df=edited_df,
        max_mode=max_mode,
    )

    return FrequencyEditorState(
        measured_frequencies_hz=edited_measured_frequencies_hz,
        use_mask=edited_use_mask,
    )


def build_frequency_editor_dataframe(
    measured_frequencies_hz: list[Optional[float]],
    use_mask: list[bool],
    theoretical_frequencies_hz: list[float],
    max_mode: int,
) -> pd.DataFrame:
    """
    周波数編集用 DataFrame を生成する。

    Args:
        measured_frequencies_hz:
            実測周波数列 [Hz]。
        use_mask:
            使用フラグ列。
        theoretical_frequencies_hz:
            理論周波数列 [Hz]。
        max_mode:
            最大モード次数。

    Returns:
        pd.DataFrame:
            data_editor に渡すための横持ち DataFrame。
    """
    columns: list[str] = [f"{mode}次" for mode in range(1, max_mode + 1)]

    data = {
        column: [
            measured_frequencies_hz[index],
            bool(use_mask[index]),
            float(theoretical_frequencies_hz[index]),
        ]
        for index, column in enumerate(columns)
    }

    df = pd.DataFrame(
        data=data,
        index=["実測周波数 [Hz]", "使用", "理論周波数 [Hz]"],
    )

    return df


def parse_frequency_editor_dataframe(
    df: pd.DataFrame,
    max_mode: int,
) -> tuple[list[Optional[float]], list[bool]]:
    """
    編集後 DataFrame から実測周波数列と use_mask を取り出す。

    Args:
        df:
            data_editor の編集後 DataFrame。
        max_mode:
            最大モード次数。

    Returns:
        tuple[list[Optional[float]], list[bool]]:
            - 編集後の実測周波数列
            - 編集後の use_mask

    Raises:
        ValueError:
            必要な行・列が不足している場合。
    """
    expected_index: list[str] = ["実測周波数 [Hz]", "使用", "理論周波数 [Hz]"]
    expected_columns: list[str] = [f"{mode}次" for mode in range(1, max_mode + 1)]

    for row_name in expected_index:
        if row_name not in df.index:
            raise ValueError(f"Missing required row: {row_name}")

    for column_name in expected_columns:
        if column_name not in df.columns:
            raise ValueError(f"Missing required column: {column_name}")

    measured_frequencies_hz: list[Optional[float]] = []
    use_mask: list[bool] = []

    for column_name in expected_columns:
        measured_value = df.at["実測周波数 [Hz]", column_name]
        use_value = df.at["使用", column_name]

        if pd.isna(measured_value) or measured_value == "":
            measured_frequencies_hz.append(None)
            use_mask.append(False)
        else:
            measured_frequencies_hz.append(float(measured_value))
            use_mask.append(bool(use_value))

    return measured_frequencies_hz, use_mask