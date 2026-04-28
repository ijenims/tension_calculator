# バッチ実行機能 追加の経緯と決定事項

作成日: 2026-04-28
最終更新日: 2026-04-28（scipy探索範囲変更・inf修正）

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
