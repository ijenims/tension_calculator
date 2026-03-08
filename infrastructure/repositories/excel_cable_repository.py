from pathlib import Path
from typing import Optional

import pandas as pd

from domain.models.cable_record import CableRecord
from infrastructure.repositories.cable_repository import CableRepository


class ExcelCableRepository(CableRepository):
    """
    Excel ファイルからケーブルマスタを取得する Repository。
    """

    def __init__(
        self,
        filepath: str,
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

            df.columns = [str(col).strip() for col in df.columns]

            self._validate_columns(df)

            self._df = df

        return self._df

    @staticmethod
    def _validate_columns(df: pd.DataFrame) -> None:
        required = [
            "施設名",
            "ケーブルNo.",
            "枝番",
            "単位重量",
            "ケーブル長",
            "設計張力",
        ]

        missing = [c for c in required if c not in df.columns]
        if missing:
            raise ValueError(f"Missing required columns: {missing}")

    def get_facility_names(self) -> list[str]:
        df = self._load()
        return sorted(df["施設名"].dropna().astype(str).unique().tolist())

    def get_cable_numbers(
        self,
        facility_name: str,
    ) -> list[str]:
        df = self._load()

        filtered = df[df["施設名"] == facility_name]

        return sorted(
            filtered["ケーブルNo."].dropna().astype(str).unique().tolist()
        )

    def get_branch_numbers(
        self,
        facility_name: str,
        cable_no: str,
    ) -> list[str]:
        df = self._load()

        filtered = df[
            (df["施設名"] == facility_name)
            & (df["ケーブルNo."] == cable_no)
        ]

        return sorted(
            filtered["枝番"].dropna().astype(str).unique().tolist()
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
            (df["施設名"] == facility_name)
            & (df["ケーブルNo."] == cable_no)
            & (df["枝番"] == branch_no)
        ]

        if len(filtered) == 0:
            raise ValueError("Cable record not found.")

        if len(filtered) > 1:
            raise ValueError("Duplicate cable records found.")

        row = filtered.iloc[0]

        measured = self._extract_frequencies(row, max_mode)

        design_rigidity = (
            float(row["設計剛性"])
            if "設計剛性" in row and pd.notna(row["設計剛性"])
            else None
        )

        xi = (
            float(row["ξ"])
            if "ξ" in row and pd.notna(row["ξ"])
            else None
        )

        return CableRecord(
            facility_name=str(row["施設名"]),
            cable_no=str(row["ケーブルNo."]),
            branch_no=str(row["枝番"]),
            unit_weight_kg_per_m=float(row["単位重量"]),
            cable_length_m=float(row["ケーブル長"]),
            design_tension_kN=float(row["設計張力"]),
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