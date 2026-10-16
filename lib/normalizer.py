"""Data normalization for AGY statusline with zero dataclass overhead."""
import os
import re
import json

from .git_provider import get_git_info
from .herdr_provider import get_herdr_info, HerdrInfo
from .config import StatuslineConfig

class QuotaInfo:
    def __init__(
        self,
        available: bool = False,
        five_hour_percent: float = None,
        five_hour_reset: str = "",
        weekly_percent: float = None,
        weekly_reset: str = "",
        is_five_hour_warning: bool = False,
        is_weekly_warning: bool = False
    ):
        self.available = available
        self.five_hour_percent = five_hour_percent
        self.five_hour_reset = five_hour_reset
        self.weekly_percent = weekly_percent
        self.weekly_reset = weekly_reset
        self.is_five_hour_warning = is_five_hour_warning
        self.is_weekly_warning = is_weekly_warning

class ContextInfo:
    def __init__(
        self,
        used_percentage: float = 0.0,
        tokens_used: int = 0,
        tokens_total: int = 0,
        tokens_display: str = "",
        progress_bar: str = "",
        is_warning: bool = False
    ):
        self.used_percentage = used_percentage
        self.tokens_used = tokens_used
        self.tokens_total = tokens_total
        self.tokens_display = tokens_display
        self.progress_bar = progress_bar
        self.is_warning = is_warning

class NormalizedData:
    def __init__(self):
        self.project_name: str = ""
        self.git_branch: str = "no-git"
        self.git_dirty: bool = False
        self.model_name: str = "unknown"
        self.thinking_level: str = ""
        self.context: ContextInfo = ContextInfo()
        self.quota: QuotaInfo = QuotaInfo()
        self.execution_mode: str = "NORMAL"
        self.permission_mode: str = "STRICT"
        self.is_yolo: bool = False
        self.agent_state: str = "IDLE"
        self.subagents_count: int = 0
        self.task_count: int = 0
        self.session_id: str = ""
        self.herdr: HerdrInfo = HerdrInfo()
        self.terminal_width: int = 80

def _format_tokens(num: int) -> str:
    """Format token number nicely (e.g. 1500 -> 1.5K, 1048576 -> 1.0M)."""
    if num >= 1_000_000:
        val = num / 1_000_000
        return f"{val:.1f}M" if val < 10 else f"{int(round(val))}M"
    if num >= 1_000:
        val = num / 1_000
        return f"{val:.1f}K" if val < 10 else f"{int(round(val))}K"
    return str(num)

def _format_reset_time(seconds) -> str:
    """Convert reset seconds into human-readable countdown like '2h 4m'."""
    if seconds is None:
        return ""
    try:
        sec = int(seconds)
    except Exception:
        return ""
    if sec <= 0:
        return ""
    hours = sec // 3600
    minutes = (sec % 3600) // 60
    if hours > 24:
        days = hours // 24
        return f"{days}d {hours % 24}h"
    if hours > 0:
        return f"{hours}h {minutes}m"
    if minutes > 0:
        return f"{minutes}m"
    return f"{sec}s"

def _make_progress_bar(percentage: float, width: int = 10, use_unicode: bool = True, style: str = "dots", is_warning: bool = False) -> str:
    """Generate a sleek, low-profile terminal progress bar without chunky or tall blocks."""
    pct = max(0.0, min(100.0, percentage))
    filled_len = int(round(width * pct / 100.0))
    empty_len = width - filled_len
    if not use_unicode or style == "ascii":
        return "=" * filled_len + "." * empty_len

    RESET = "\033[0m"
    c_filled = "\033[38;5;208m" if is_warning else "\033[38;5;81m"
    c_empty = "\033[38;5;240m"

    if style == "squares":
        f_char, e_char = "■", "□"
    elif style == "mini":
        f_char, e_char = "▄", "─"
    elif style == "solid":
        f_char, e_char = "█", "─"
    else:  # default "dots"
        f_char, e_char = "●", "○"

    return f"{c_filled}{f_char * filled_len}{c_empty}{e_char * empty_len}{RESET}"

def normalize_data(payload: dict, config: StatuslineConfig) -> NormalizedData:
    """Normalize raw payload and environmental metadata into clean structured presentation data."""
    data = NormalizedData()
    
    # 1. Project & Directory
    cwd = payload.get("cwd") or (payload.get("workspace", {}).get("current_dir") if isinstance(payload.get("workspace"), dict) else "")
    if not cwd:
        cwd = os.getcwd()
    data.project_name = os.path.basename(os.path.abspath(cwd)) or "workspace"

    # 2. Git metadata
    vcs = payload.get("vcs") if isinstance(payload.get("vcs"), dict) else None
    data.git_branch, data.git_dirty = get_git_info(cwd, vcs)

    # 3. Model & Thinking / Effort level
    model_obj = payload.get("model")
    if isinstance(model_obj, dict):
        display = model_obj.get("display_name") or model_obj.get("id") or "unknown"
        effort = model_obj.get("effort") or ""
    elif isinstance(model_obj, str):
        display = model_obj
        effort = ""
    else:
        display = "unknown"
        effort = ""
    
    # Clean up model name
    data.model_name = display
    if effort:
        effort_clean = effort.capitalize()
        if f"({effort.lower()})" not in display.lower() and f" {effort.lower()}" not in display.lower():
            data.thinking_level = effort_clean
        else:
            data.thinking_level = ""
    else:
        data.thinking_level = ""

    # 4. Context window
    ctx_obj = payload.get("context_window")
    if isinstance(ctx_obj, dict):
        pct = float(ctx_obj.get("used_percentage") or 0.0)
        tokens_in = int(ctx_obj.get("total_input_tokens") or 0)
        tokens_out = int(ctx_obj.get("total_output_tokens") or 0)
        tokens_used = tokens_in + tokens_out
        tokens_total = int(ctx_obj.get("context_window_size") or 0)
        if tokens_used == 0 and "used_tokens" in ctx_obj:
            tokens_used = int(ctx_obj["used_tokens"])
        if tokens_total == 0 and "total_tokens" in ctx_obj:
            tokens_total = int(ctx_obj["total_tokens"])

        if pct == 0.0 and tokens_total > 0 and tokens_used > 0:
            pct = (tokens_used / tokens_total) * 100.0

        is_warning = pct >= config.context_warning_threshold
        tokens_str = f"{_format_tokens(tokens_used)}/{_format_tokens(tokens_total)}" if tokens_total > 0 else ""
        bar = _make_progress_bar(
            pct,
            width=8 if config.layout == "compact" else 10,
            use_unicode=config.use_icons,
            style=config.bar_style,
            is_warning=is_warning
        )

        data.context = ContextInfo(
            used_percentage=round(pct, 1),
            tokens_used=tokens_used,
            tokens_total=tokens_total,
            tokens_display=tokens_str,
            progress_bar=bar,
            is_warning=is_warning
        )

    # 5. Quota
    quota_obj = payload.get("quota")
    if isinstance(quota_obj, dict) and quota_obj:
        is_gemini = bool(re.search(r"gemini", data.model_name, re.IGNORECASE))
        bucket_5h_key = "gemini-5h" if is_gemini else "3p-5h"
        bucket_wk_key = "gemini-weekly" if is_gemini else "3p-weekly"
        
        b_5h = quota_obj.get(bucket_5h_key) or quota_obj.get("gemini-5h") or quota_obj.get("3p-5h")
        b_wk = quota_obj.get(bucket_wk_key) or quota_obj.get("gemini-weekly") or quota_obj.get("3p-weekly") or quota_obj.get("gemini-argon-wtu-weekly")

        q_info = QuotaInfo(available=True)
        if isinstance(b_5h, dict):
            rem_frac = b_5h.get("remaining_fraction")
            if rem_frac is not None:
                q_info.five_hour_percent = round(float(rem_frac) * 100.0, 1)
                q_info.is_five_hour_warning = q_info.five_hour_percent <= config.quota_warning_threshold
            q_info.five_hour_reset = _format_reset_time(b_5h.get("reset_in_seconds"))

        if isinstance(b_wk, dict):
            rem_frac = b_wk.get("remaining_fraction")
            if rem_frac is not None:
                q_info.weekly_percent = round(float(rem_frac) * 100.0, 1)
                q_info.is_weekly_warning = q_info.weekly_percent <= config.quota_warning_threshold
            q_info.weekly_reset = _format_reset_time(b_wk.get("reset_in_seconds"))

        data.quota = q_info

    # 6. Execution mode (CycleMode from Shift+Tab) & Permissions
    raw_mode = (
        payload.get("cycle_mode")
        or payload.get("mode")
        or payload.get("execution_mode")
        or payload.get("agent_mode")
        or payload.get("agentMode")
        or ""
    )
    raw_mode_str = str(raw_mode).lower().strip()
    if raw_mode_str in ("accept-edits", "edit", "edits"):
        data.execution_mode = "EDIT"
    elif raw_mode_str in ("plan", "planning"):
        data.execution_mode = "PLAN"
    elif raw_mode_str in ("auto", "automatic"):
        data.execution_mode = "AUTO"
    elif raw_mode_str in ("battle", "best-of-n"):
        data.execution_mode = "BATTLE"
    elif raw_mode_str in ("default", "normal"):
        data.execution_mode = "NORMAL"
    elif raw_mode_str:
        data.execution_mode = raw_mode_str.upper()
    else:
        data.execution_mode = "NORMAL"

    perm_mode = payload.get("permission_mode") or ""
    if not perm_mode:
        settings_path = os.path.expanduser("~/.gemini/antigravity-cli/settings.json")
        if os.path.isfile(settings_path):
            try:
                with open(settings_path, "r") as f:
                    s_data = json.load(f)
                perm_mode = s_data.get("toolPermission", "")
            except Exception:
                pass
    
    perm_str = str(perm_mode).lower()
    if "always-proceed" in perm_str or "yolo" in perm_str:
        data.permission_mode = "YOLO"
        data.is_yolo = True
    elif "request-review" in perm_str or "review" in perm_str:
        data.permission_mode = "REVIEW"
        data.is_yolo = False
    elif "strict" in perm_str:
        data.permission_mode = "STRICT"
        data.is_yolo = False
    else:
        data.permission_mode = perm_mode.upper() if perm_mode else "NORMAL"
        data.is_yolo = False

    # 7. Agent state
    raw_state = payload.get("agent_state") or "idle"
    data.agent_state = str(raw_state).upper()

    # 8. Subagents & Tasks
    subagents = payload.get("subagents")
    if isinstance(subagents, list):
        data.subagents_count = len([s for s in subagents if isinstance(s, dict) and s.get("status") in ("running", "active")])
    data.task_count = int(payload.get("task_count") or 0)

    # 9. Session / Conversation ID
    sess = payload.get("session_id") or payload.get("conversation_id") or os.environ.get("ANTIGRAVITY_CONVERSATION_ID", "")
    if sess:
        data.session_id = str(sess)[:8]

    # 10. Herdr & Terminal
    data.herdr = get_herdr_info()
    data.terminal_width = int(payload.get("terminal_width") or 80)

    return data
