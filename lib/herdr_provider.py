"""Herdr environment metadata provider with zero-cost environment queries."""
import os

class HerdrInfo:
    def __init__(self, is_herdr: bool = False, pane_id: str = "", tab_id: str = "", workspace_id: str = ""):
        self.is_herdr = is_herdr
        self.pane_id = pane_id
        self.tab_id = tab_id
        self.workspace_id = workspace_id

def get_herdr_info() -> HerdrInfo:
    """
    Extracts Herdr metadata from environment variables without making socket queries.
    """
    pane_id = os.environ.get("HERDR_PANE_ID", "")
    tab_id = os.environ.get("HERDR_TAB_ID", "")
    workspace_id = os.environ.get("HERDR_WORKSPACE_ID", "")
    is_herdr = bool(os.environ.get("HERDR_ENV") == "1" or pane_id)

    return HerdrInfo(
        is_herdr=is_herdr,
        pane_id=pane_id,
        tab_id=tab_id,
        workspace_id=workspace_id
    )
