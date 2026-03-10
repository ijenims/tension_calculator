from typing import List, Optional, Tuple

import streamlit as st


def render_frequency_editor(
    case_key: str,
    theoretical_freqs: List[float],
    measured_freqs: List[Optional[float]],
    use_mask: List[bool],
) -> Tuple[List[Optional[float]], List[bool]]:
    """
    周波数編集UI（横配置）

    上から
    1. モード見出し
    2. 理論周波数（表示のみ）
    3. 実測周波数（編集可）
    4. 使用チェックボックス
    """
    max_mode: int = len(theoretical_freqs)

    st.subheader("周波数編集")

    # --- ヘッダ行 ---
    header_cols = st.columns(max_mode + 1)
    header_cols[0].markdown("")
    for i in range(max_mode):
        header_cols[i + 1].markdown(f"**{i + 1}次**")

    # --- 理論周波数行 ---
    theory_cols = st.columns(max_mode + 1)
    theory_cols[0].markdown("**理論周波数 [Hz]**")
    for i, f in enumerate(theoretical_freqs):
        theory_cols[i + 1].write(f"{f:.4f}")

    # --- 実測周波数行 ---
    measured_cols = st.columns(max_mode + 1)
    measured_cols[0].markdown("**実測周波数 [Hz]**")

    new_measured: List[Optional[float]] = []
    for i in range(max_mode):
        default_value: str = "" if measured_freqs[i] is None else f"{measured_freqs[i]}"
        val: str = measured_cols[i + 1].text_input(
            label=f"{i + 1}次 実測周波数",
            value=default_value,
            label_visibility="collapsed",
            key=f"obs_freq_{case_key}_{i}",
        )

        if val.strip() == "":
            new_measured.append(None)
        else:
            try:
                new_measured.append(float(val))
            except ValueError:
                new_measured.append(None)

    # --- 使用行 ---
    use_cols = st.columns(max_mode + 1)
    use_cols[0].markdown("**使用**")

    new_mask: List[bool] = []
    for i in range(max_mode):
        checked: bool = use_cols[i + 1].checkbox(
            label=f"{i + 1}次 使用",
            value=use_mask[i],
            label_visibility="collapsed",
            key=f"use_freq_{case_key}_{i}",
        )
        new_mask.append(checked)

    return new_measured, new_mask