from abc import ABC, abstractmethod

from domain.models.cable_record import CableRecord


class CableRepository(ABC):
    """
    ケーブルマスタ取得の抽象リポジトリ。

    データソース（Excel / SQLite / API）に依存しない
    インターフェースを定義する。
    """

    @abstractmethod
    def get_facility_names(self) -> list[str]:
        """
        施設名一覧を取得する。
        """
        raise NotImplementedError

    @abstractmethod
    def get_cable_numbers(
        self,
        facility_name: str,
    ) -> list[str]:
        """
        指定施設に属するケーブルNo一覧を取得する。
        """
        raise NotImplementedError

    @abstractmethod
    def get_branch_numbers(
        self,
        facility_name: str,
        cable_no: str,
    ) -> list[str]:
        """
        指定ケーブルの枝番一覧を取得する。
        """
        raise NotImplementedError

    @abstractmethod
    def get_cable_record(
        self,
        facility_name: str,
        cable_no: str,
        branch_no: str,
        max_mode: int = 7,
    ) -> CableRecord:
        """
        ケーブル情報を取得する。

        Returns
        -------
        CableRecord
        """
        raise NotImplementedError