"""Formatter and renderer for AGY statusline."""
import re
from typing import List, Dict, Any, Tuple
from .config import StatuslineConfig
from .normalizer import NormalizedData

# ANSI Color Helpers
RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"

# Themes palette mapping
THEMES = {
    "default": {
        "mode": "\033[33m",          # Yellow (Normal)
        "mode_edit": "\033[33m",     # Yellow (Edit)
        "mode_plan": "\033[36m",     # Cyan (Plan)
        "mode_auto": "\033[35m",     # Magenta (Auto)
        "mode_battle": "\033[91m",   # Bright Red (Battle)
        "yolo": "\033[91m",          # Bright Red
        "strict": "\033[92m",        # Bright Green
        "review": "\033[95m",        # Bright Magenta
        "project": "\033[97m",       # Crisp White
        "git": "\033[32m",           # Green
        "git_dirty": "\033[33m",     # Yellow
        "no_git": "\033[38;5;248m",  # Crisp Silver Gray
        "model": "\033[96m",         # Crisp Cyan
        "effort": "\033[95m",        # Bright Magenta
        "context": "\033[36m",       # Cyan
        "ctx_warn": "\033[91m",      # Bright Red
        "quota_ok": "\033[32m",      # Green
        "quota_warn": "\033[91m",    # Bright Red
        "state_idle": "\033[38;5;250m",# Crisp Silver
        "state_work": "\033[92m",    # Bright Green
        "state_think": "\033[93m",   # Bright Yellow
        "pane": "\033[95m",          # Bright Magenta
        "session": "\033[38;5;248m", # Crisp Silver
        "sep": "\033[38;5;245m",     # Crisp Neutral Gray Dot
    },
    "pastel": {
        "mode": "\033[38;5;222m",       # Soft Peach
        "yolo": "\033[38;5;210m",       # Soft Coral
        "strict": "\033[38;5;151m",     # Soft Mint
        "review": "\033[38;5;183m",     # Soft Lavender
        "project": "\033[38;5;153m",    # Soft Sky Blue
        "git": "\033[38;5;151m",        # Soft Sage
        "git_dirty": "\033[38;5;222m",  # Soft Yellow
        "no_git": "\033[38;5;244m",     # Muted Grey
        "model": "\033[38;5;111m",      # Pastel Blue
        "effort": "\033[38;5;183m",     # Pastel Lavender
        "context": "\033[38;5;152m",    # Pastel Cyan
        "ctx_warn": "\033[38;5;203m",   # Pastel Red
        "quota_ok": "\033[38;5;151m",   # Soft Mint
        "quota_warn": "\033[38;5;203m", # Pastel Red
        "state_idle": "\033[38;5;244m", # Muted Grey
        "state_work": "\033[38;5;151m", # Soft Mint
        "state_think": "\033[38;5;222m",# Soft Peach
        "pane": "\033[38;5;183m",       # Lavender
        "session": "\033[38;5;244m",    # Grey
        "sep": "\033[38;5;240m",        # Dim Grey
    },
    "nord": {
        "mode": "\033[38;5;221m",       # Nord13 Yellow
        "yolo": "\033[38;5;167m",       # Nord11 Red
        "strict": "\033[38;5;108m",     # Nord14 Green
        "review": "\033[38;5;139m",     # Nord15 Purple
        "project": "\033[38;5;110m",    # Nord9 Frost Blue
        "git": "\033[38;5;108m",        # Nord14 Green
        "git_dirty": "\033[38;5;221m",  # Nord13 Yellow
        "no_git": "\033[38;5;242m",     # Polar Night Grey
        "model": "\033[38;5;111m",      # Nord10 Frost
        "effort": "\033[38;5;139m",     # Nord15 Purple
        "context": "\033[38;5;109m",    # Nord8 Frost Teal
        "ctx_warn": "\033[38;5;167m",   # Nord11 Red
        "quota_ok": "\033[38;5;108m",   # Nord14 Green
        "quota_warn": "\033[38;5;167m", # Nord11 Red
        "state_idle": "\033[38;5;242m", # Nord3 Grey
        "state_work": "\033[38;5;108m", # Nord14 Green
        "state_think": "\033[38;5;221m",# Nord13 Yellow
        "pane": "\033[38;5;139m",       # Nord15 Purple
        "session": "\033[38;5;242m",    # Nord3 Grey
        "sep": "\033[38;5;238m",        # Nord1 Polar
    },
    "solarized": {
        "mode": "\033[33m",             # Yellow
        "yolo": "\033[31m",             # Red
        "strict": "\033[32m",           # Green
        "review": "\033[35m",           # Magenta
        "project": "\033[36m",          # Cyan
        "git": "\033[32m",              # Green
        "git_dirty": "\033[33m",        # Yellow
        "no_git": "\033[90m",           # Base01
        "model": "\033[34m",            # Blue
        "effort": "\033[35m",           # Magenta
        "context": "\033[36m",          # Cyan
        "ctx_warn": "\033[1;31m",       # Bold Red
        "quota_ok": "\033[32m",         # Green
        "quota_warn": "\033[1;31m",     # Bold Red
        "state_idle": "\033[90m",       # Base01
        "state_work": "\033[32m",       # Green
        "state_think": "\033[33m",      # Yellow
        "pane": "\033[35m",             # Violet
        "session": "\033[90m",          # Base01
        "sep": "\033[90m",              # Base01
    },
    "monochrome": {
        "mode": "", "yolo": "", "strict": "", "review": "", "project": "",
        "git": "", "git_dirty": "", "no_git": "", "model": "", "effort": "",
        "context": "", "ctx_warn": "", "quota_ok": "", "quota_warn": "",
        "state_idle": "", "state_work": "", "state_think": "", "pane": "",
        "session": "", "sep": "",
    }
}

# Icon sets
ICONS = {
    "unicode": {
        "mode": "⚡ ",
        "yolo": "🔓 ",
        "strict": "🛡 ",
        "review": "📝 ",
        "project": "📁 ",
        "git": "🌿 ",
        "model": "🤖 ",
        "context": "🧠 ",
        "quota_5h": "⏱ ",
        "quota_wk": "📅 ",
        "work": "⚙ ",
        "think": "🤔 ",
        "idle": "💤 ",
        "subagent": "👥 ",
        "task": "📌 ",
        "pane": "🪟 ",
        "session": "🔗 ",
        "warn": "⚠ ",
        "sep": " · "
    },
    "ascii": {
        "mode": "",
        "yolo": "[YOLO] ",
        "strict": "[STRICT] ",
        "review": "[REVIEW] ",
        "project": "[DIR] ",
        "git": "[GIT] ",
        "model": "[MODEL] ",
        "context": "[CTX] ",
        "quota_5h": "[5h] ",
        "quota_wk": "[7d] ",
        "work": "[WORK] ",
        "think": "[THINK] ",
        "idle": "[IDLE] ",
        "subagent": "[AGENTS] ",
        "task": "[TASKS] ",
        "pane": "[PANE] ",
        "session": "[SESS] ",
        "warn": "(!) ",
        "sep": " | "
    }
}

def strip_ansi(text: str) -> str:
    """Strip ANSI sequences to compute visible length."""
    return re.sub(r'\x1b\[[0-9;]*m', '', text)

def truncate_to_width(text: str, max_w: int) -> str:
    """Truncate text with ANSI codes so visible width <= max_w."""
    if max_w <= 0:
        return ""
    vis_len = len(strip_ansi(text))
    if vis_len <= max_w:
        return text
    
    # Simple truncate by stripping codes, truncating, then appending reset
    plain = strip_ansi(text)
    return plain[:max_w-1] + "…"

class StatuslineRenderer:
    def __init__(self, config: StatuslineConfig):
        self.config = config
        raw_theme = THEMES.get(config.theme.lower(), THEMES["default"])
        self.theme = raw_theme.copy()
        if getattr(config, "bold", False):
            # If bold is explicitly requested, inject bold code
            for k, v in self.theme.items():
                if v and "\033[" in v:
                    if v.startswith("\033[38;5;"):
                        self.theme[k] = f"\033[1m{v}"
                    elif not v.startswith("\033[1"):
                        self.theme[k] = v.replace("\033[", "\033[1;", 1)
        else:
            # Ensure no bold codes in any theme palette
            for k, v in self.theme.items():
                if v:
                    v = re.sub(r'\033\[1;([0-9;]+m)', r'\033[\1', v)
                    v = v.replace("\033[1m", "")
                    self.theme[k] = v

        self.icons = ICONS["unicode"].copy() if config.use_icons else ICONS["ascii"].copy()
        if getattr(config, "separator", None):
            self.icons["sep"] = config.separator
        self.reset = "" if config.theme.lower() == "monochrome" else RESET

    def _c(self, key: str, text: str) -> str:
        """Wrap text in color key."""
        color = self.theme.get(key, "")
        if not color or not text:
            return text
        return f"{color}{text}{self.reset}"

    def render(self, data: NormalizedData) -> str:
        """Render normalized data into formatted terminal statusline."""
        # Determine effective layout
        width = data.terminal_width or 80
        layout = self.config.layout.lower()
        if layout == "auto":
            if width >= 120:
                layout = "wide"
            elif width >= 80:
                layout = "medium"
            else:
                layout = "compact"

        if width < 50:
            lines = self._render_ultra_compact(data, width)
        elif layout == "wide":
            lines = self._render_wide(data, width)
        elif layout == "medium":
            lines = self._render_medium(data, width)
        else:
            lines = self._render_compact(data, width)

        # Apply max_lines restriction
        if self.config.max_lines > 0 and len(lines) > self.config.max_lines:
            lines = lines[:self.config.max_lines]

        return "\n".join(lines)

    def _render_wide(self, data: NormalizedData, width: int) -> List[str]:
        """Wide layout (>= 120 cols). Rich 2-line display."""
        sep = self._c("sep", self.icons["sep"])
        
        # --- Line 1: Mode · Perms · Project · Git · Agent State · Subagents · Herdr · Session ---
        l1_parts = []
        if self.config.show_permissions:
            mode_color = "mode"
            m_icon = self.icons["mode"]
            if data.execution_mode == "EDIT":
                mode_color = "mode_edit"
                m_icon = "✏️ " if self.config.use_icons else "[EDIT] "
            elif data.execution_mode == "PLAN":
                mode_color = "mode_plan"
                m_icon = "📋 " if self.config.use_icons else "[PLAN] "
            elif data.execution_mode == "AUTO":
                mode_color = "mode_auto"
                m_icon = "🤖 " if self.config.use_icons else "[AUTO] "
            elif data.execution_mode == "BATTLE":
                mode_color = "mode_battle"
                m_icon = "⚔️ " if self.config.use_icons else "[BATTLE] "
            elif data.execution_mode == "NORMAL":
                mode_color = "mode"
                m_icon = "⚡ " if self.config.use_icons else "[NORM] "
            
            p_badge = self._c(mode_color, f"{m_icon}{data.execution_mode}")
            
            # Permission Mode
            if data.is_yolo:
                perm_badge = self._c("yolo", f"{self.icons['yolo']}YOLO")
            elif data.permission_mode == "STRICT":
                perm_badge = self._c("strict", f"{self.icons['strict']}STRICT")
            else:
                perm_badge = self._c("review", f"{self.icons['review']}{data.permission_mode}")
            l1_parts.append(f"{p_badge} {perm_badge}")

        # Project
        proj_badge = self._c("project", f"{self.icons['project']}{data.project_name}")
        l1_parts.append(proj_badge)

        # Git
        if self.config.show_git:
            if data.git_branch == "no-git":
                git_badge = self._c("no_git", f"{self.icons['git']}no-git")
            else:
                dirty_marker = "*" if data.git_dirty else ""
                color_key = "git_dirty" if data.git_dirty else "git"
                git_badge = self._c(color_key, f"{self.icons['git']}{data.git_branch}{dirty_marker}")
            l1_parts.append(git_badge)

        # Agent State
        if self.config.show_agent_state:
            state = data.agent_state
            if state in ("WORKING", "TOOL"):
                state_badge = self._c("state_work", f"{self.icons['work']}{state}")
            elif state in ("THINKING",):
                state_badge = self._c("state_think", f"{self.icons['think']}{state}")
            else:
                state_badge = self._c("state_idle", f"{self.icons['idle']}{state}")
            l1_parts.append(state_badge)

        # Subagents
        if data.subagents_count > 0:
            l1_parts.append(self._c("pane", f"{self.icons['subagent']}{data.subagents_count} subagents"))

        # Tasks
        if data.task_count > 0:
            l1_parts.append(self._c("state_work", f"{self.icons['task']}{data.task_count} tasks"))

        # Herdr
        if self.config.show_herdr and data.herdr.is_herdr and data.herdr.pane_id:
            l1_parts.append(self._c("pane", f"{self.icons['pane']}{data.herdr.pane_id}"))

        # Session ID
        if self.config.show_session and data.session_id:
            l1_parts.append(self._c("session", f"{self.icons['session']}{data.session_id}"))

        line1 = sep.join(l1_parts)

        # --- Line 2: Model (Effort) · Context Window · Quota 5h · Quota Weekly ---
        l2_parts = []
        if self.config.show_model:
            model_text = data.model_name
            if data.thinking_level:
                model_text += f" ({data.thinking_level})"
            l2_parts.append(self._c("model", f"{self.icons['model']}{model_text}"))

        if self.config.show_context:
            ctx = data.context
            c_icon = self.icons["context"]
            pct_str = self._c("ctx_warn" if ctx.is_warning else "context", f"{ctx.used_percentage}%")
            ctx_text = f"{c_icon}Context {pct_str} {ctx.progress_bar}"
            if ctx.tokens_display:
                ctx_text += f" {self._c('session', ctx.tokens_display)}"
            l2_parts.append(ctx_text)

        if self.config.show_quota and data.quota.available:
            q = data.quota
            if q.five_hour_percent is not None:
                q5_color = "quota_warn" if q.is_five_hour_warning else "quota_ok"
                q5_str = f"{self.icons['quota_5h']}5h {q.five_hour_percent}% left"
                if q.five_hour_reset:
                    q5_str += f" ({q.five_hour_reset})"
                l2_parts.append(self._c(q5_color, q5_str))

            if q.weekly_percent is not None:
                qwk_color = "quota_warn" if q.is_weekly_warning else "quota_ok"
                qwk_str = f"{self.icons['quota_wk']}7d {q.weekly_percent}% left"
                if q.weekly_reset:
                    qwk_str += f" ({q.weekly_reset})"
                l2_parts.append(self._c(qwk_color, qwk_str))

        line2 = sep.join(l2_parts)
        return [truncate_to_width(line1, width), truncate_to_width(line2, width)]

    def _render_medium(self, data: NormalizedData, width: int) -> List[str]:
        """Medium layout (80 - 119 cols). Balanced 2-line display."""
        sep = self._c("sep", self.icons["sep"])
        
        # Line 1: Mode/Perms · Project · Git · Agent State · Herdr
        l1_parts = []
        if self.config.show_permissions:
            mode_color = "mode"
            m_icon = ""
            if data.execution_mode == "EDIT":
                mode_color = "mode_edit"
                m_icon = "✏️ " if self.config.use_icons else ""
            elif data.execution_mode == "PLAN":
                mode_color = "mode_plan"
                m_icon = "📋 " if self.config.use_icons else ""
            elif data.execution_mode == "AUTO":
                mode_color = "mode_auto"
                m_icon = "🤖 " if self.config.use_icons else ""
            elif data.execution_mode == "BATTLE":
                mode_color = "mode_battle"
                m_icon = "⚔️ " if self.config.use_icons else ""
            elif data.execution_mode == "NORMAL":
                mode_color = "mode"
                m_icon = "⚡ " if self.config.use_icons else ""

            perm_label = "YOLO" if data.is_yolo else data.permission_mode
            color_key = "yolo" if data.is_yolo else ("strict" if data.permission_mode == "STRICT" else "review")
            l1_parts.append(f"{self._c(mode_color, f'{m_icon}{data.execution_mode}')} {self._c(color_key, perm_label)}")

        l1_parts.append(self._c("project", f"{self.icons['project']}{data.project_name}"))

        if self.config.show_git:
            if data.git_branch == "no-git":
                l1_parts.append(self._c("no_git", "no-git"))
            else:
                dirty = "*" if data.git_dirty else ""
                c = "git_dirty" if data.git_dirty else "git"
                l1_parts.append(self._c(c, f"{self.icons['git']}{data.git_branch}{dirty}"))

        if self.config.show_agent_state:
            state = data.agent_state
            if state in ("WORKING", "TOOL"):
                state_badge = self._c("state_work", f"{self.icons['work']}{state}")
            elif state in ("THINKING",):
                state_badge = self._c("state_think", f"{self.icons['think']}{state}")
            else:
                state_badge = self._c("state_idle", f"{self.icons['idle']}{state}")
            l1_parts.append(state_badge)

        if self.config.show_herdr and data.herdr.is_herdr and data.herdr.pane_id:
            l1_parts.append(self._c("pane", f"{self.icons['pane']}{data.herdr.pane_id}"))

        line1 = sep.join(l1_parts)

        # Line 2: Model · Context · Quota
        l2_parts = []
        if self.config.show_model:
            # Shorten model name if long (e.g. Gemini 3.8 Flash (Medium) -> Gemini Flash)
            m_short = data.model_name.replace("Gemini 3.8 Flash (Medium)", "Gemini 3.8 Flash")
            if data.thinking_level:
                m_short += f" ({data.thinking_level[:3]})"
            l2_parts.append(self._c("model", f"{self.icons['model']}{m_short}"))

        if self.config.show_context:
            ctx = data.context
            c_icon = self.icons["context"]
            pct_str = self._c("ctx_warn" if ctx.is_warning else "context", f"{ctx.used_percentage}%")
            tokens_str = f" {self._c('session', ctx.tokens_display)}" if ctx.tokens_display else ""
            l2_parts.append(f"{c_icon}{pct_str} {ctx.progress_bar}{tokens_str}")

        if self.config.show_quota and data.quota.available:
            q = data.quota
            if q.five_hour_percent is not None:
                c = "quota_warn" if q.is_five_hour_warning else "quota_ok"
                l2_parts.append(self._c(c, f"{self.icons['quota_5h']}5h {q.five_hour_percent}%"))
            if q.weekly_percent is not None:
                c = "quota_warn" if q.is_weekly_warning else "quota_ok"
                l2_parts.append(self._c(c, f"{self.icons['quota_wk']}7d {q.weekly_percent}%"))

        line2 = sep.join(l2_parts)
        return [truncate_to_width(line1, width), truncate_to_width(line2, width)]

    def _render_compact(self, data: NormalizedData, width: int) -> List[str]:
        """Compact layout (< 80 cols). Essential metrics only."""
        sep = self._c("sep", " ")
        
        # Line 1: Mode/YOLO · Proj (branch) · State
        dirty = "*" if data.git_dirty else ""
        branch = "" if data.git_branch == "no-git" else f" ({data.git_branch}{dirty})"
        l1 = f"{self._c('mode', data.execution_mode[:4])} {self._c('yolo' if data.is_yolo else 'strict', data.permission_mode[:4])} {self._c('project', data.project_name[:12])}{self._c('git', branch)} {self._c('state_work' if data.agent_state != 'IDLE' else 'state_idle', data.agent_state[:4])}"
        
        # Line 2: Model · Ctx% · Quota 5h
        m_name = data.model_name.replace("Gemini ", "").replace(" (Medium)", "")[:10]
        ctx_pct = f"{data.context.used_percentage}%"
        q_str = f"5h:{data.quota.five_hour_percent}%" if data.quota.five_hour_percent is not None else ""
        l2 = f"{self._c('model', m_name)} {self._c('context', ctx_pct)} {self._c('quota_ok', q_str)}"

        return [truncate_to_width(l1, width), truncate_to_width(l2, width)]

    def _render_ultra_compact(self, data: NormalizedData, width: int) -> List[str]:
        """Ultra-compact layout (< 50 cols). Pure dense single line."""
        dirty = "*" if data.git_dirty else ""
        q = f"{int(data.quota.five_hour_percent)}%" if data.quota.five_hour_percent is not None else "-"
        text = f"{data.execution_mode[:3]}|{data.project_name[:8]}|{data.context.used_percentage}%|5h:{q}"
        return [truncate_to_width(text, width)]
