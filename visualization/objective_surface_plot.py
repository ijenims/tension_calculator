from typing import Optional

import numpy as np
import plotly.graph_objects as go


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
    title: str = "Objective Surface (MSE)",
    show_contours: bool = True,
    orthographic: bool = True,
    aspect_ratio: tuple[float, float, float] = (1.0, 1.0, 1.0),
    mark_min: bool = True,
) -> go.Figure:
    """
    objective surface (k, b, MSE) の 3D グラフを生成する。

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

    Returns:
        go.Figure:
            Plotly Figure オブジェクト。

    Raises:
        ValueError:
            K, B, Z の shape が一致しない場合。
    """
    if not (K.shape == B.shape == Z.shape):
        raise ValueError("K, B, Z must have the same shape.")

    Z_plot: np.ndarray = np.where(np.isfinite(Z), Z, np.nan)

    surface = go.Surface(
        x=K,
        y=B,
        z=Z_plot,
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
            zaxis_title="MSE",
            # zaxis=dict(type="log"),  # z軸を対数スケールにする
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
        min_point = find_min_on_surface(K=K, B=B, Z=Z)
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