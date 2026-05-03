"""
cable_master.xlsx の全レコードに対してグリッドサーチ最適化を実行し、
元データ + 計算結果5列を cable_master_and_grid_result.xlsx に出力する。

Usage:
    python batch_runner.py
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


def _save(df: pd.DataFrame) -> None:
    df.to_excel(OUTPUT_FILEPATH, index=False, engine="openpyxl")


def main() -> None:
    repo = ExcelCableRepository(
        filepath=MASTER_FILEPATH,
        sheet_name=MASTER_SHEET_NAME,
    )

    result_columns = ["k", "b", "tension_kN", "rigidity_Nm2", "mse"]

    # 出力ファイルが既にあれば途中結果を引き継ぐ
    if OUTPUT_FILEPATH.exists():
        source_df = pd.read_excel(OUTPUT_FILEPATH, engine="openpyxl")
        print(f"Resume from {OUTPUT_FILEPATH}")
    else:
        source_df = repo._load().copy()
        for col in result_columns:
            source_df[col] = None

    service = OptimizationService()
    total = len(source_df)

    for idx, row in source_df.iterrows():
        # 計算済みならスキップ
        if pd.notna(row.get("k")):
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

            # use_mask: 実測周波数があるモードだけ True
            use_mask = [f is not None for f in cable.measured_frequencies_hz]

            # 探索条件: デフォルト（多段 grid は optimizer 側の刻みを使用）
            condition = SearchCondition.default()

            result = service.optimize(
                cable=cable,
                use_mask=use_mask,
                condition=condition,
            )

            source_df.at[idx, "k"] = result.k
            source_df.at[idx, "b"] = result.b
            source_df.at[idx, "tension_kN"] = result.tension_kN
            source_df.at[idx, "rigidity_Nm2"] = result.rigidity_Nm2
            source_df.at[idx, "mse"] = result.mse

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
