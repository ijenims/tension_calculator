from typing import Optional

import streamlit as st
from streamlit.runtime.uploaded_file_manager import UploadedFile


def render_master_file_uploader() -> Optional[UploadedFile]:
    """
    ケーブルマスタ Excel ファイルのアップロードUIを描画する。

    Returns
    -------
    Optional[UploadedFile]
        アップロード済みファイル。
        未アップロード時は None を返す。
    """
    st.subheader("マスタファイル")

    uploaded_file = st.file_uploader(
        label="cable_master.xlsx をアップロード",
        type=["xlsx"],
        accept_multiple_files=False,
        key="master_file_uploader",
    )

    return uploaded_file