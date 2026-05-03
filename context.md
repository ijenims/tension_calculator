# バッチ実行機能 追加の経緯と決定事項

作成日: 2026-04-28
最終更新日: 2026-05-03（多段グリッド探索・デフォルト探索範囲）

---

## やりたいこと

`cable_master.xlsx` の全レコードに対して最適化を一括実行し、
結果を新しいExcelファイルに出力する。

## 決定事項

### 出力ファイル

- ファイル名: `cable_master_and_grid_result.xlsx`
- 出力先: `data/`
- 元のマスタデータ全列をそのまま残し、末尾に計算結果列を追加

### 記録する計算結果

grid 結果（5列）:

| 列名 | 内容 |
|------|------|
| k | 張力係数 |
| b | 剛性係数 |
| tension_kN | 推定張力 |
| rigidity_Nm2 | 推定剛性 |
| mse | 最小二乗誤差 |

scipy 結果（5列、grid 列の後ろに追加）:

| 列名 | 内容 |
|------|------|
| k_scipy | 張力係数 |
| b_scipy | 剛性係数 |
| tension_kN_scipy | 推定張力 |
| rigidity_Nm2_scipy | 推定剛性 |
| mse_scipy | 最小二乗誤差 |

最終的な列構成: `[元マスタ列] | [grid結果5列] | [scipy結果5列]`

### 探索条件

grid（`batch_runner.py`）:
- `grid_step_b` のみ `0.01` に変更（デフォルトは `0.1`）
- それ以外はすべて `SearchCondition.default()` のまま
  - k_min=0.5, k_max=2.0, b_min=-10.0, b_max=10.0
  - grid_step_k=0.01
  - weight_mode="none", use_normalized_mse=False

scipy（`batch_runner_scipy.py`）:
- `method` を `"scipy"` に変更
- 探索範囲を拡大: k_min=0.1, k_max=3.0, b_min=-20.0, b_max=20.0
- それ以外はデフォルトのまま

### max_mode

- `10` 固定（デフォルトは7だが、歯抜けが多いため10で全モードカバー）

### use_mask

- 実測周波数が入っているモードだけ `True`、`None` のモードは `False`
- 自動生成（手動指定なし）

### design_rigidity_Nm2 の扱い

- マスタに値がなくても `ExcelCableRepository.get_cable_record()` 内で
  `DesignRigidityCalculator.calculate_from_unit_weight()` により単位重量から自動補完される
- そのため全レコード計算可能（スキップ不要）

### グラフ

- 不要（バッチ実行なので可視化しない）

### 元ファイルの保護

- `cable_master.xlsx` は上書きしない
- 新規ファイル `cable_master_and_grid_result.xlsx` に出力

## 実装

### batch_runner.py（grid search）

- CLI実行: `python batch_runner.py`
- Streamlit UI には手を加えない
- エラーが出たレコードはスキップし、結果列は空欄のまま残す

### batch_runner_scipy.py（scipy）

- CLI実行: `python batch_runner_scipy.py`
- `batch_runner.py` が完了済みであること（出力ファイルが存在すること）が前提
- 既存の `cable_master_and_grid_result.xlsx` を読み込み、scipy 結果列を追加

### 実行順序

```
python batch_runner.py          # 1. grid（先に実行）
python batch_runner_scipy.py    # 2. scipy（後から追加）
```

### 中間保存・レジューム（両バッチ共通）

- 10件ごとに出力ファイルへ中間保存（`SAVE_EVERY = 10`）
- 途中で強制終了しても、最後の中間保存時点までの結果はファイルに残る
- 再実行時、結果列（grid は `k`、scipy は `k_scipy`）が埋まっているレコードはスキップして未計算分だけ実行する（レジューム対応）

## バグ修正

### objective_function の inf → 1e10 修正

- ファイル: `domain/evaluation/objective_function.py`
- 変更内容: 計算不能な k, b の組み合わせで `np.inf` を返していた箇所を `1e10` に変更
- 原因: scipy の L-BFGS-B がライン探索中に inf を踏むと、ステップ縮小を試みず初期値で打ち切ってしまう問題
- 影響: grid search には実質影響なし（inf でも 1e10 でも最小値選択の結果は同じ）
- Streamlit アプリの 3D サーフェスプロットで inf だった領域が有限値になるが、表示上はむしろ改善

---

## 3D サーフェス表示（MSE 軸）とサイドバー UI（2026-05-02）

### 経緯

- `objective_function` の **inf → 1e10** により、グリッド上の「計算不能・不正」領域も **1e10 前後の有限値**としてサーフェスに載るようになった。
- 実データの MSE は小さいが、**ペナルティセルがグリッドの半分近くを占めるケース**があり、従来の **全セルに対する 99% 分位**だけでは MSE 軸の上限が巨大のままになり、3D が読みにくい問題が残った。
- **計算（最適化）本体は変更しない。** 対応は **表示専用**に限定する。

### 表示ロジック（`visualization/objective_surface_plot.py`）

- 描画用の **Z（MSE）を上限 `z_cap` でクリップ**し、`scene.zaxis.range = [0, z_cap]` で軸を固定する。
- **最適点マーカー**は元の `Z` に対する `find_min_on_surface` のまま。手動上限が最適値より狭い場合は `z_cap` を `mse_min` まで引き上げてマーカーが軸外に出ないようにする。
- **自動 `z_cap`（`z_cap_max` 未指定時）**
  - まず **有限かつ `Z < 1e9`** のセルだけを集める（`objective_function` のペナルティ **1e10** より下の閾値 **1e9** で混ぜない）。
  - その集合で **99% 分位**を取る。
  - **該当セルが 0 件**のときは、従来どおり **全有限セル**にフォールバックする。
- **手動上書き**: 正の値を渡すとその値を `z_cap` として用いる（上級者向け）。

### サイドバー UI（`ui/components/sidebar.py`）

- **「3D サーフェス（grid）」** エクスパンダ内に **MSE 表示上限**のテキスト入力（空欄＝自動）。
- 配置は **最適化実行ボタンの直下・保存セクションの上**（サイドバー最下部ではない）。
- **条件入力**（施設名・ケーブル No・枝番）のいずれかが変わったら、手入力の MSE 上限は **空欄にリセット**し、自動キャップに戻す。

### 補足

- 分位数計算と 1e9 マスクは **いずれも O(n)** で、グリッド評価に比べれば無視できるコスト。
- 詳細な設計メモ・バッチ機能の経緯は引き続き本ファイルを参照する。

---

## テキストファイルの文字コード（README / context など）

- リポジトリ内の **Markdown・ソース以外のプレーンテキストも含め、UTF-8（BOM なし推奨）** で保存する。
- **UTF-16** で保存すると、Cursor / VS Code で「バイナリまたは未対応のエンコード」と出てエディタに表示されないことがある（GitHub 側の制限ではなく、保存形式の問題）。
- **Cursor / VS Code での設定**
  - `settings.json` に `"files.encoding": "utf8"` を入れて既定を UTF-8 にする（ワークスペース用 `.vscode/settings.json` でも可）。
  - 一度 UTF-16 になってしまったファイルは、ステータスバーのエンコーディング表示から **「Save with Encoding」→ UTF-8** で直せる。

---

## 多段グリッド探索（grid）

`method == "grid"` のとき、全域一発の細かいグリッドではなく **粗 → 中 → 細** の3段で評価し、評価回数を抑える。

**パラメータの単一ソース**: `config/grid_multistage.py`（刻み・窓幅・top-N・枠拡張・3D 用サーフェス刻み）。

### 段別設定（既定値・ファイルで変更）

| 段 | k 刻み | b 刻み | 窓 |
|----|--------|--------|-----|
| 粗 | 0.05 | 1.0 | `SearchCondition` の k/b 全域 |
| 中 | 0.01 | 0.10 | 粗の **上位8点** 各中心で k±0.10, b±3.0（全域へクリップ） |
| 細 | 0.005 | 0.01 | 中の **上位8点** 各中心で k±0.03, b±0.30（全域へクリップ） |

- 同一 (k,b) はキャッシュし二重評価しない。
- 3段終了後、最適解が枠の端から **近い**とき枠を広げる（k は ±0.25、b は ±10）。最大 **4 ラウンド**まで繰り返し、次ラウンドは再び粗から実行。
- 「端からの距離」のしきい値は `BOUNDARY_MARGIN_K` / `B` と `BOUNDARY_MARGIN_MAX_FRACTION_OF_SPAN` の **小さい方**（区間幅×比率）で cap する。**k の区間幅が狭い（例: 2）のとき、絶対値 1.0 だけだと全域が「端」扱いになり、k_min/k_max が意図せず広がっていた**ため、この cap を入れている。

### デフォルト探索範囲（`config/defaults.py`）

- k: **0.5〜2.5**、b: **-50〜50**（UI の初期値・リセット値と一致）。
- サイドバーの **k_min / k_max / b_min / b_max** は `SearchCondition` 経由で多段探索と 3D の**表示範囲のベース**に使われる（枠拡張が走った場合は**拡張後の枠**で 3D も描く）。
- サイドバーの `grid_step_k` / `grid_step_b` は **scipy 用**および `evaluate_surface` で刻みを省略したときのフォールバック用。**多段 grid と 3D（grid）の刻みは `grid_multistage.py` の `SURFACE_GRID_STEP_*` 等**。

### 3D サーフェス

- `optimize_with_surface` は多段で最適化したあと、(1) **拡張後の最終探索枠**上で粗い `SURFACE_GRID_STEP_*` により全域 `evaluate_surface`、(2) **最適解周辺**（`SURFACE_ZOOM_*` の半幅・細い刻み）でもう一度 `evaluate_surface` し、**粗用と細用の2組**を返す。
- Streamlit サイドバー「3D サーフェス（grid）」のラジオで **全体（粗）／最小付近（細）** を切替。細は最適化実行直後のセッションにだけ保持される。

### バッチ

- `batch_runner.py` は `SearchCondition.default()` のみ使用（以前の `grid_step_b = 0.01` 上書きは削除）。

## ここから先は最後のチャット原文(要約してない)
Q. あと、最小値付近を拡大するとやっぱりギザギザになるよな。グラフ表示用のグリッド幅やからしゃあないやろけど、最小値付近だけでも表示グリッドを小さくすることって結構大変？

A. **そこまで大変ではない**（表示だけの話なので、ロジックは素直）。

## やりたいことのイメージ

いまは **全域を粗い格子 1 枚**で `Surface` しているので、谷が細いとギザつく。  
**最小付近だけ刻みを細かくする**のは、だいたい次のどれか。

| 方針 | 実装の重さ | 内容 |
|------|------------|------|
| **A. 細い `Surface` をもう 1 枚足す** | 小〜中 | 粗い全域＋`(k_opt,b_opt)` 周りの矩形だけ `evaluate_surface` を細刻み。Plotly で **trace を 2 本**（同じ `Figure`）。拡大パッチが少し盛り上がって見えるのを、透明度や色でごまかす。 |
| **B. 表示を「拡大ビュー」に切替** | 小 | トグルで「全体（粗）／最小付近（細）」を切り替え。実装は `evaluate_surface` を 2 パターン呼ぶだけ。 |
| **C. 不規則格子** | 中 | `Mesh3d` など。見た目は柔軟だが、コードとデバッグがやや増える。 |

## 負荷の目安

- **`evaluate_surface` は既にある**ので、**細い窓を決めてもう 1 回呼ぶ**だけ。
- 窓は例: `k_opt ± 0.2`, `b_opt ± 2` を `last_search_bounds` でクリップ、刻みは `grid_multistage.py` に `SURFACE_FINE_STEP_*` を足す程度。
- **大変なのは仕様決め**（窓の幅・細さ・粗面を残すか／拡大だけにするか）で、**実装は 1〜2 ファイル（`optimization_service` + `app` or プロット）で収まる**ことが多い。

まとめると、「最小付近だけ表示グリッドを細かくする」は **よくある対応で、難易度は中の下**くらい。やるなら **B（切替）か A（二重 Surface）** がおすすめ。

対応：内容（方針 B）
config/grid_multistage.py

SURFACE_ZOOM_K_HALF = 0.25、SURFACE_ZOOM_B_HALF = 5.0
SURFACE_ZOOM_GRID_STEP_K = 0.01、SURFACE_ZOOM_GRID_STEP_B = 0.2
optimize_with_surface

従来どおり全域・粗の K,B,Z に加え、最適解中心の窓で細い格子の Kz,Bz,Zz を計算して返す（窓が狭すぎるときは最小スパンを確保）。
session_state_manager

set_surface_data(..., K_zoom=..., B_zoom=..., Z_zoom=...)
get_surface_data() は 6 要素 (K,B,Z,Kz,Bz,Zz)。
サイドバー「3D サーフェス（grid）」

ラジオ 「全体（粗）」／「最小付近（細）」（key=sidebar_surface_view_mode、既定 coarse）。
app.py

表示時にモードに応じて K,B,Z を差し替え、タイトルを
Mean Squared Error（全体・粗）
Mean Squared Error（最小付近・細）
細データが無い（未実行・古いセッションなど）は自動で粗にフォールバック。
context.md

上記の挙動を追記。
注意: 「最小付近」は 最適化実行時にだけ再計算される。ラジオだけ切り替えた場合はキャッシュした粗／細を使い回す。細を見る前に必ず grid で最適化実行が必要。

## 次の一手
Q. そういえばUIのgrid_step_k, grid_step_b入力は意味ないんやったな