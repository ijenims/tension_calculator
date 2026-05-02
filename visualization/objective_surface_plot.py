from typing import Optional

import numpy as np
import plotly.graph_objects as go

DEFAULT_SURFACE_Z_PERCENTILE = 99.0

# objective_function のペナルティ(1e10)より下。cap 推定では Z >= これを混ぜない。
Z_CAP_PENALTY_EXCLUSION_GE = 1e9


def compute_z_cap_percentile(Z: np.ndarray, percentile: float = DEFAULT_SURFACE_Z_PERCENTILE) -> float:
    """
    有限の Z 値から表示用の上限（分位数）を求める。

    グリッドの多くがペナルティ(1e10)のとき、分位が潰れないよう
    Z < Z_CAP_PENALTY_EXCLUSION_GE のセルだけで分位数を取る。
    その集合が空なら従来どおり全有限セルにフォールバックする。

    点が少ない・退化ケースでは最小値より少し上まで確保する。
    """
    finite: np.ndarray = Z[np.isfinite(Z)]
    if finite.size == 0:
        return 1.0

    reasonable: np.ndarray = finite[finite < Z_CAP_PENALTY_EXCLUSION_GE]
    vals: np.ndarray = reasonable if reasonable.size > 0 else finite

    cap: float = float(np.percentile(vals, percentile))
    z_min: float = float(np.min(vals))
    if cap <= z_min:
        cap = z_min * 1.01 if z_min > 0 else 1.0
    return cap


def find_min_on_surface(
    K: np.ndarray,
    B: np.ndarray,
    Z: np.ndarray,
) -> Optional[tuple[float, float, float]]:
    """
    3次元サーフェス上の有限値のうち、最小点を求める。

    Args:
        K:
            k の meshgrid。
        B:
            b の meshgrid。
        Z:
            各格子点の MSE。

    Returns:
        Optional[tuple[float, float, float]]:
            (k_min, b_min, mse_min)
            有効な点が存在しない場合は None。

    Raises:
        ValueError:
            K, B, Z の shape が一致しない場合。
    """
    if not (K.shape == B.shape == Z.shape):
        raise ValueError("K, B, Z must have the same shape.")

    valid_mask: np.ndarray = np.isfinite(Z)
    if not np.any(valid_mask):
        return None

    flat_k: np.ndarray = K[valid_mask].ravel()
    flat_b: np.ndarray = B[valid_mask].ravel()
    flat_z: np.ndarray = Z[valid_mask].ravel()

    min_index: int = int(np.argmin(flat_z))

    return (
        float(flat_k[min_index]),
        float(flat_b[min_index]),
        float(flat_z[min_index]),
    )


def create_objective_surface_plot(
    K: np.ndarray,
    B: np.ndarray,
    Z: np.ndarray,
    title: str = "Mean Squared Error",
    show_contours: bool = True,
    orthographic: bool = True,
    aspect_ratio: tuple[float, float, float] = (1.0, 1.0, 1.0),
    mark_min: bool = True,
    z_cap_max: Optional[float] = None,
    z_percentile: float = DEFAULT_SURFACE_Z_PERCENTILE,
) -> go.Figure:
    """
    objective surface (k, b, MSE) の 3D グラフを生成する。

    表示専用に Z を上限クリップし、Z 軸レンジをその上限に合わせる。
    最適解マーカーは元の Z に基づく find_min_on_surface の結果を使う。

    Args:
        K:
            k の meshgrid。
        B:
            b の meshgrid。
        Z:
            各格子点の MSE。
        title:
            グラフタイトル。
        show_contours:
            等高線を表示するかどうか。
        orthographic:
            True の場合、正投影で表示する。
        aspect_ratio:
            3D グラフの軸比率 (x, y, z)。
        mark_min:
            最小点をマークするかどうか。
        z_cap_max:
            None のときは Z の有限値のうち Z < 1e9 のセルだけで z_percentile 分位を取り
            表示上限を自動決定（該当セルが無いときは全有限セルにフォールバック）。
            正の値を渡すとその値を表示上限として用いる。
        z_percentile:
            z_cap_max が None のときの分位数（デフォルト 99）。

    Returns:
        go.Figure:
            Plotly Figure オブジェクト。

    Raises:
        ValueError:
            K, B, Z の shape が一致しない場合。
    """
    if not (K.shape == B.shape == Z.shape):
        raise ValueError("K, B, Z must have the same shape.")

    z_cap: float = (
        float(z_cap_max)
        if z_cap_max is not None and z_cap_max > 0
        else compute_z_cap_percentile(Z, percentile=z_percentile)
    )

    min_point = find_min_on_surface(K=K, B=B, Z=Z) if mark_min else None
    if min_point is not None:
        _, _, mse_min = min_point
        if mse_min > z_cap:
            z_cap = float(mse_min)

    Z_clipped: np.ndarray = np.where(
        np.isfinite(Z),
        np.minimum(Z, z_cap),
        np.nan,
    )
    Z_plot: np.ndarray = Z_clipped

    surface = go.Surface(
        x=K,
        y=B,
        z=Z_plot,
        colorscale='rainbow',  # カラースケール
        opacity=0.8,    # サーフェスの透明度
        contours=dict(
            x=dict(show=show_contours, project_x=True),
            y=dict(show=show_contours, project_y=True),
            z=dict(
                show=show_contours, 
                usecolormap=True, 
                highlightcolor="lime",    # 等高線の色
                project_z=True),
        ),
        hovertemplate=(
            "k=%{x:.4f}<br>"
            "b=%{y:.4f}<br>"
            "MSE=%{z:.6g}"
            "<extra></extra>"
        ),
        name="MSE Surface",
    )

    fig = go.Figure(data=[surface])

    fig.update_layout(
        title=title,
        height=900,    # グラフの高さ
        scene=dict(
            xaxis_title="k",
            yaxis_title="b",
            zaxis=dict(title="MSE", range=[0.0, z_cap]),
            aspectratio=dict(
                x=aspect_ratio[0],
                y=aspect_ratio[1],
                z=aspect_ratio[2],
            ),
            aspectmode="manual",
            camera=dict(
                projection=dict(
                    type="orthographic" if orthographic else "perspective"
                )
            ),
        ),
    )

    if mark_min:
        if min_point is not None:
            k_min, b_min, mse_min = min_point

            fig.add_trace(
                go.Scatter3d(
                    x=[k_min],
                    y=[b_min],
                    z=[mse_min],
                    mode="markers+text",
                    text=[f"({k_min:.4g}, {b_min:.4g}, {mse_min:.4g})"],
                    textposition="top center",
                    marker=dict(size=4, symbol="circle"),
                    name="Minimum",
                    hovertemplate=(
                        "k=%{x:.4f}<br>"
                        "b=%{y:.4f}<br>"
                        "MSE=%{z:.6g}"
                        "<extra></extra>"
                    ),
                )
            )

    return fig