"""Configuration manager for agy-statusline without heavy imports."""
import os
import json

class StatuslineConfig:
    def __init__(
        self,
        theme: str = "default",
        layout: str = "auto",
        max_lines: int = 2,
        show_git: bool = True,
        show_model: bool = True,
        show_context: bool = True,
        show_quota: bool = True,
        show_permissions: bool = True,
        show_agent_state: bool = True,
        show_session: bool = True,
        show_herdr: bool = True,
        use_icons: bool = True,
        separator: str = " · ",
        bar_style: str = "dots",  # dots (●○), squares (■□), mini (▄─), solid (█─), ascii (=.)
        bold: bool = False,
        context_warning_threshold: float = 75.0,
        quota_warning_threshold: float = 20.0,
    ):
        self.theme = theme
        self.layout = layout
        self.max_lines = max_lines
        self.show_git = show_git
        self.show_model = show_model
        self.show_context = show_context
        self.show_quota = show_quota
        self.show_permissions = show_permissions
        self.show_agent_state = show_agent_state
        self.show_session = show_session
        self.show_herdr = show_herdr
        self.use_icons = use_icons
        self.separator = separator
        self.bar_style = bar_style
        self.bold = bold
        self.context_warning_threshold = context_warning_threshold
        self.quota_warning_threshold = quota_warning_threshold

    @classmethod
    def load(cls) -> "StatuslineConfig":
        config = cls()
        config_path = os.environ.get("AGY_STATUSLINE_CONFIG")
        if not config_path:
            config_path = os.path.expanduser("~/.config/agy-statusline/config.json")
        
        if os.path.isfile(config_path):
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if isinstance(data, dict):
                    for k, v in data.items():
                        if hasattr(config, k):
                            setattr(config, k, v)
            except Exception:
                pass
        
        # Environment variable overrides
        if os.environ.get("AGY_STATUSLINE_THEME"):
            config.theme = os.environ["AGY_STATUSLINE_THEME"]
        if os.environ.get("AGY_STATUSLINE_LAYOUT"):
            config.layout = os.environ["AGY_STATUSLINE_LAYOUT"]
        if os.environ.get("AGY_STATUSLINE_NO_ICONS") == "1":
            config.use_icons = False
        if os.environ.get("AGY_STATUSLINE_SEPARATOR"):
            config.separator = os.environ["AGY_STATUSLINE_SEPARATOR"]
        if os.environ.get("AGY_STATUSLINE_BOLD") == "1":
            config.bold = True
        elif os.environ.get("AGY_STATUSLINE_BOLD") == "0":
            config.bold = False
            
        return config
