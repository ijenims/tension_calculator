from pathlib import Path
from typing import Optional

import pandas as pd

from config.defaults import (
    FACILITY,
    CABLE_NO,
    BRANCH_NO,
    UNIT_WEIGHT,
    CABLE_LENGTH,
    DESIGN_TENSION,
    DESIGN_RIGIDITY,
    XI,
)
from domain.models.cable_record import CableRecord
from infrastructure.repositories.cable_repository import CableRepository
from domain.physics.design_rigidity_calculator import DesignRigidityCalculator
from domain.physics.xi_calculator import XiCalculator


class ExcelCableRepository(CableRepository):
    """
    Excel ファイルからケーブルマスタを取得する Repository。
    """

    def __init__(
        self,
        filepath: str | Path,
        sheet_name: Optional[str] = None,
    ) -> None:
        self._filepath = Path(filepath)
        self._sheet_name = sheet_name
        self._df: Optional[pd.DataFrame] = None

    def _load(self) -> pd.DataFrame:
        if self._df is None:
            if not self._filepath.exists():
                raise FileNotFoundError(f"Master file not found: {self._filepath}")

            df = pd.read_excel(
                self._filepath,
                sheet_name=self._sheet_name,
                engine="openpyxl",
            )

            if isinstance(df, dict):
                df = list(df.values())[0]

            df.columns = [str(col).strip() for col in df.columns]

            self._validate_columns(df)

            self._df = df

        return self._df

    @staticmethod
    def _validate_columns(df: pd.DataFrame) -> None:
        required = [
            FACILITY,
            CABLE_NO,
            BRANCH_NO,
            UNIT_WEIGHT,
            CABLE_LENGTH,
            DESIGN_TENSION,
        ]

        missing = [c for c in required if c not in df.columns]
        if missing:
            raise ValueError(f"Missing required columns: {missing}")

    def get_facility_names(self) -> list[str]:
        df = self._load()
        return sorted(df[FACILITY].dropna().astype(str).unique().tolist())

    def get_cable_numbers(
        self,
        facility_name: str,
    ) -> list[str]:
        df = self._load()

        filtered = df[df[FACILITY] == facility_name]

        return sorted(
            filtered[CABLE_NO].dropna().astype(str).unique().tolist()
        )

    def get_branch_numbers(
        self,
        facility_name: str,
        cable_no: str,
    ) -> list[str]:
        df = self._load()

        filtered = df[
            (df[FACILITY] == facility_name)
            & (df[CABLE_NO] == cable_no)
        ]

        return sorted(
            filtered[BRANCH_NO].dropna().astype(str).unique().tolist()
        )

    def get_cable_record(
        self,
        facility_name: str,
        cable_no: str,
        branch_no: str,
        max_mode: int = 7,
    ) -> CableRecord:

        df = self._load()

        filtered = df[
            (df[FACILITY].astype(str) == str(facility_name))
            & (df[CABLE_NO].astype(str) == str(cable_no))
            & (df[BRANCH_NO].astype(str) == str(branch_no))
        ]

        if len(filtered) == 0:
            raise ValueError("Cable record not found.")

        if len(filtered) > 1:
            raise ValueError("Duplicate cable records found.")

        row = filtered.iloc[0]

        measured = self._extract_frequencies(row, max_mode)

        design_rigidity = (
            float(row[DESIGN_RIGIDITY])
            if DESIGN_RIGIDITY in row and pd.notna(row[DESIGN_RIGIDITY])
            else None
        )

        if design_rigidity is None:
            design_rigidity = DesignRigidityCalculator.calculate_from_unit_weight(
                unit_weight_kg_per_m=float(row[UNIT_WEIGHT])
            )

        xi = (
            float(row[XI])
            if XI in row and pd.notna(row[XI])
            else None
        )

        if xi is None:
            xi = XiCalculator.calculate(
                cable_length_m=float(row[CABLE_LENGTH]),
                tension_kN=float(row[DESIGN_TENSION]),
                rigidity_Nm2=design_rigidity,
            )

        return CableRecord(
            facility_name=str(row[FACILITY]),
            cable_no=str(row[CABLE_NO]),
            branch_no=str(row[BRANCH_NO]),
            unit_weight_kg_per_m=float(row[UNIT_WEIGHT]),
            cable_length_m=float(row[CABLE_LENGTH]),
            design_tension_kN=float(row[DESIGN_TENSION]),
            design_rigidity_Nm2=design_rigidity,
            xi=xi,
            measured_frequencies_hz=measured,
            max_mode=max_mode,
        )

    @staticmethod
    def _extract_frequencies(
        row: pd.Series,
        max_mode: int,
    ) -> list[Optional[float]]:

        frequencies: list[Optional[float]] = []

        for i in range(1, max_mode + 1):

            col = f"f{i}"

            if col in row and pd.notna(row[col]):
                frequencies.append(float(row[col]))
            else:
                frequencies.append(None)

        return frequencies