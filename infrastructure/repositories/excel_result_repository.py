from pathlib import Path
from datetime import datetime

import pandas as pd

from domain.models.cable_record import CableRecord
from domain.models.calculation_result import CalculationResult
from domain.models.search_condition import SearchCondition


class ExcelResultRepository:
    """
    計算結果を Excel に保存する Repository。
    """

    def __init__(
        self,
        filepath: str,
        sheet_name: str = "results",
    ) -> None:
        self._filepath = Path(filepath)
        self._sheet_name = sheet_name

    def append_result(
        self,
        cable: CableRecord,
        result: CalculationResult,
        condition: SearchCondition,
        method: str,
    ) -> None:
        """
        計算結果を Excel に追記する。
        """

        row = self._build_row(
            cable=cable,
            result=result,
            condition=condition,
            method=method,
        )

        df_new = pd.DataFrame([row])

        if self._filepath.exists():

            df_old = pd.read_excel(
                self._filepath,
                sheet_name=self._sheet_name,
                engine="openpyxl",
            )

            df = pd.concat([df_old, df_new], ignore_index=True)

        else:

            df = df_new

        df.to_excel(
            self._filepath,
            sheet_name=self._sheet_name,
            index=False,
            engine="openpyxl",
        )

    def _build_row(
        self,
        cable: CableRecord,
        result: CalculationResult,
        condition: SearchCondition,
        method: str,
    ) -> dict:

        row: dict = {}

        # ---------- 識別 ----------
        row["facility_name"] = cable.facility_name
        row["cable_no"] = cable.cable_no
        row["branch_no"] = cable.branch_no

        # ---------- ケーブル諸元 ----------
        row["unit_weight_kg_per_m"] = cable.unit_weight_kg_per_m
        row["cable_length_m"] = cable.cable_length_m
        row["design_tension_kN"] = cable.design_tension_kN
        row["design_rigidity_Nm2"] = cable.design_rigidity_Nm2
        row["xi"] = result.xi

        # ---------- 観測周波数 ----------
        for i in range(10):

            key = f"f{i+1}_obs"

            if i < len(result.measured_frequencies_hz):
                row[key] = result.measured_frequencies_hz[i]
            else:
                row[key] = None

        # ---------- 使用モード ----------
        for i in range(10):

            key = f"use_{i+1}"

            if i < len(result.use_mask):
                row[key] = result.use_mask[i]
            else:
                row[key] = False

        # ---------- 理論周波数 ----------
        for i in range(10):

            key = f"f{i+1}_theory"

            if i < len(result.theoretical_frequencies_hz):
                row[key] = result.theoretical_frequencies_hz[i]
            else:
                row[key] = None

        # ---------- 計算結果 ----------
        row["k"] = result.k
        row["b"] = result.b
        row["tension_kN"] = result.tension_kN
        row["rigidity_Nm2"] = result.rigidity_Nm2
        row["mse"] = result.mse

        # ---------- 条件 ----------
        row["method"] = method
        row["search_method"] = condition.method
        row["k_min"] = condition.k_min
        row["k_max"] = condition.k_max
        row["b_min"] = condition.b_min
        row["b_max"] = condition.b_max
        row["grid_step_k"] = condition.grid_step_k
        row["grid_step_b"] = condition.grid_step_b
        row["weight_mode"] = condition.weight_mode
        row["use_normalized_mse"] = condition.use_normalized_mse

        # ---------- 時刻 ----------
        row["saved_at"] = datetime.now().isoformat()

        return row