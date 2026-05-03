"""
grid 手法の多段探索・3D サーフェス表示用の格子設定。

Streamlit の「探索設定」にある k_min/k_max/b_min/b_max は SearchCondition 経由で
多段探索と 3D の表示範囲のベースになる（範囲拡張後は拡張後の枠で表示）。
grid_step_k / grid_step_b（UI）は scipy 用・evaluate_surface 省略時のフォールバック用。
"""

# ----- 粗段 -----
COARSE_GRID_STEP_K = 0.05
COARSE_GRID_STEP_B = 1.0

# ----- 中段（粗の上位 N 点を中心） -----
MEDIUM_K_HALF_WIDTH = 0.10
MEDIUM_GRID_STEP_K = 0.01
MEDIUM_B_HALF_WIDTH = 3.0
MEDIUM_GRID_STEP_B = 0.10

# ----- 細段（中の上位 N 点を中心） -----
FINE_K_HALF_WIDTH = 0.03
FINE_GRID_STEP_K = 0.005
FINE_B_HALF_WIDTH = 0.30
FINE_GRID_STEP_B = 0.01

MULTISTAGE_TOP_N = 8

# ----- 探索枠の自動拡張 -----
# 最適解が「枠の端からこれ以内」なら拡張を検討（絶対値の上限）
BOUNDARY_MARGIN_K = 1.0
BOUNDARY_MARGIN_B = 1.0
# k の区間幅が狭いとき、上記 1.0 のままだと全域が「端」とみなされて
# k_min/k_max がユーザ指定を無視して広がる。区間幅に対する比率で cap する。
BOUNDARY_MARGIN_MAX_FRACTION_OF_SPAN = 0.25

EXPAND_K = 0.25
EXPAND_B = 10.0
MAX_RANGE_EXPANSION_ROUNDS = 4

# ----- 3D 表示用 evaluate_surface の刻み（最適化後、最終枠上で評価） -----
SURFACE_GRID_STEP_K = COARSE_GRID_STEP_K
SURFACE_GRID_STEP_B = COARSE_GRID_STEP_B

# ----- 3D 「最小付近」表示（UI で「全体」と切替） -----
SURFACE_ZOOM_K_HALF = 0.25
SURFACE_ZOOM_B_HALF = 5.0
SURFACE_ZOOM_GRID_STEP_K = 0.01
SURFACE_ZOOM_GRID_STEP_B = 0.2
