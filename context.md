# バッチ実行機能 追加の経緯と決定事項

## やりたいこと

`cable_master.xlsx` の全レコードに対してグリッドサーチ最適化を一括実行し、
結果を新しいExcelファイルに出力する。

## 決定事項

### 出力ファイル

- ファイル名: `cable_master_and_grid_result.xlsx`
- 出力先: `data/`
- 元のマスタデータ全列をそのまま残し、末尾に計算結果5列を追加

### 記録する計算結果（5項目）

| 列名 | 内容 |
|------|------|
| k | 張力係数 |
| b | 剛性係数 |
| tension_kN | 推定張力 |
| rigidity_Nm2 | 推定剛性 |
| mse | 最小二乗誤差 |

### 探索条件

- 探索方法: grid search（デフォルト）
- `grid_step_b` のみ `0.01` に変更（デフォルトは `0.1`）
- それ以外はすべて `SearchCondition.default()` のまま
  - k_min=0.5, k_max=2.0, b_min=-10.0, b_max=10.0
  - grid_step_k=0.01
  - weight_mode="none", use_normalized_mse=False

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

- `batch_runner.py` をプロジェクトルートに作成
- CLI実行: `python batch_runner.py`
- Streamlit UI には手を加えない
- エラーが出たレコードはスキップし、結果列は空欄のまま残す

### 中間保存・レジューム

- 10件ごとに出力ファイルへ中間保存（`SAVE_EVERY = 10`）
- 途中で強制終了しても、最後の中間保存時点までの結果はファイルに残る
- 再実行時、出力ファイルが既に存在すればそれを読み込み、`k` 列が埋まっているレコードはスキップして未計算分だけ実行する（レジューム対応）
