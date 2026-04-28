"""
cable_master_and_grid_result.xlsx に scipy 最適化の結果5列を追加する。

前提: batch_runner.py (grid) が完了済みで出力ファイルが存在すること。

Usage:
    python batch_runner_scipy.py
"""

from pathlib import Path

import pandas as pd

from config.defaults import (
    FACILITY,
    CABLE_NO,
    BRANCH_NO,
    MASTER_FILEPATH,
    MASTER_SHEET_NAME,
)
from domain.models.search_condition import SearchCondition
from infrastructure.repositories.excel_cable_repository import ExcelCableRepository
from services.optimization_service import OptimizationService

OUTPUT_FILEPATH = Path("data") / "cable_master_and_grid_result.xlsx"
MAX_MODE = 10
SAVE_EVERY = 10

RESULT_COLUMNS = [
    "k_scipy",
    "b_scipy",
    "tension_kN_scipy",
    "rigidity_Nm2_scipy",
    "mse_scipy",
]


def _save(df: pd.DataFrame) -> None:
    df.to_excel(OUTPUT_FILEPATH, index=False, engine="openpyxl")


def main() -> None:
    if not OUTPUT_FILEPATH.exists():
        raise FileNotFoundError(
            f"{OUTPUT_FILEPATH} が見つかりません。先に batch_runner.py を実行してください。"
        )

    repo = ExcelCableRepository(
        filepath=MASTER_FILEPATH,
        sheet_name=MASTER_SHEET_NAME,
    )

    source_df = pd.read_excel(OUTPUT_FILEPATH, engine="openpyxl")

    # scipy 結果列がなければ追加
    for col in RESULT_COLUMNS:
        if col not in source_df.columns:
            source_df[col] = None

    service = OptimizationService()
    total = len(source_df)

    for idx, row in source_df.iterrows():
        # 計算済みならスキップ
        if pd.notna(row.get("k_scipy")):
            continue

        facility = str(row[FACILITY])
        cable_no = str(row[CABLE_NO])
        branch_no = str(row[BRANCH_NO])

        label = f"[{idx + 1}/{total}] {facility} / {cable_no} / {branch_no}"

        try:
            cable = repo.get_cable_record(
                facility_name=facility,
                cable_no=cable_no,
                branch_no=branch_no,
                max_mode=MAX_MODE,
            )

            use_mask = [f is not None for f in cable.measured_frequencies_hz]

            condition = SearchCondition.default()
            condition.method = "scipy"
            condition.k_min = 0.1
            condition.k_max = 3.0
            condition.b_min = -20.0
            condition.b_max = 20.0

            result = service.optimize(
                cable=cable,
                use_mask=use_mask,
                condition=condition,
            )

            source_df.at[idx, "k_scipy"] = result.k
            source_df.at[idx, "b_scipy"] = result.b
            source_df.at[idx, "tension_kN_scipy"] = result.tension_kN
            source_df.at[idx, "rigidity_Nm2_scipy"] = result.rigidity_Nm2
            source_df.at[idx, "mse_scipy"] = result.mse

            print(f"  OK   {label}")

        except Exception as e:
            print(f"  SKIP {label} -> {e}")

        # N件ごとに中間保存
        if (idx + 1) % SAVE_EVERY == 0:
            _save(source_df)
            print(f"  ... saved ({idx + 1}/{total})")

    # 最終保存
    _save(source_df)

    print(f"\nDone. -> {OUTPUT_FILEPATH}")


if __name__ == "__main__":
    main()
