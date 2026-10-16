# ⚡ agy-statusline

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3](https://img.shields.io/badge/Python-3.8%2B-brightgreen.svg)](https://www.python.org/)
[![Platform](https://img.shields.io/badge/Platform-Linux%20%7C%20macOS%20%7C%20Windows-lightgrey.svg)](README.md)
[![Speed](https://img.shields.io/badge/Render%20Latency-~37ms-success.svg)](README.md)

An elegant, lightning-fast, and distraction-free custom statusline (footer) for **Google Antigravity (AGY) CLI**.

---

## 📸 Preview

```text
✏️ EDIT 🔓 YOLO · 📁 fluxa · 🌿 develop* · ⚙ WORKING · 👥 2 subagents · 🪟 w1:pQ · 🔗 1ac78a98
🤖 Gemini 3.8 Flash (Medium) · 🧠 Context 11.4% ●○○○○○○○○○ 25K/218K · ⏱ 5h 86.0% left (2h 0m) · 📅 7d 78.0% left (5d 0h)
```

---

## ✨ Features

- ⚡ **Sub-50ms Latency (~37ms avg):** Zero heavy imports, direct filesystem reads, no external network calls, zero AI tokens spent.
- 🔄 **Realtime Mode Cycling (`Shift + Tab`):** Seamlessly updates mode badge (`NORMAL` $\rightarrow$ `EDIT` $\rightarrow$ `PLAN` $\rightarrow$ `AUTO` $\rightarrow$ `BATTLE`) on the fly.
- 🌿 **Ultra-Fast Git Provider:** Direct `.git/HEAD` reader (~0.05ms) with branch name, dirty `*` status, and `no-git` fallback.
- 🧠 **Elegant Context Progress Bar:** Refined dot style (`●●○○○○○○○○`) with two-tone Sky Cyan and Slate Gray palette.
- 🔲 **Flat, Crisp Typography:** Standard regular font weight (no harsh bold, no drop-shadow) with clean middle-dot (` · `) dividers.
- 🪟 **Herdr & Multi-Pane Aware:** Automatically detects and displays current pane (`w1:pQ`).
- 📐 **3 Responsive Layouts:**
  - **Wide** ($\ge 120$ cols): Full 2-line dashboard with project, git, model, quota, subagents, and session.
  - **Medium** ($80-119$ cols): Optimized single/two-line priority view.
  - **Compact** ($< 80$ cols): Ultra-compact indicator view.
- 🛡 **100% Safe & Crash-Proof:** Always exits `0`, filters API keys and sensitive tokens, automatically creates backups before modifying `settings.json`.

---

## 🚀 One-Line Installation (Cài đặt 1 câu lệnh)

### 🐧 Linux & 🍏 macOS

Using **curl**:
```bash
curl -fsSL https://raw.githubusercontent.com/truongnq/agy-statusline/main/install.sh | bash
```

Using **wget**:
```bash
wget -qO- https://raw.githubusercontent.com/truongnq/agy-statusline/main/install.sh | bash
```

### 🪟 Windows (PowerShell)

Open PowerShell and run:
```powershell
irm https://raw.githubusercontent.com/truongnq/agy-statusline/main/install.ps1 | iex
```

> **Note:** The installer automatically detects Python 3, backs up your existing `~/.gemini/antigravity-cli/settings.json`, and preserves all your models, workspaces, and permission settings intact.

---

## 📦 Offline / Air-Gapped Installation (Máy không có mạng)

For machines without internet access (e.g. secure corporate networks):

1. Export the standalone bundle on a connected machine:
   ```bash
   bash ~/.config/agy-statusline/export.sh
   ```
2. Copy `~/agy-statusline-installer.sh` to a USB drive or transfer it as text.
3. On the offline machine, simply run:
   ```bash
   bash agy-statusline-installer.sh
   ```

---

## ⚙️ Configuration

The configuration file is located at `~/.config/agy-statusline/config.json`:

```json
{
  "theme": "default",
  "layout": "auto",
  "max_lines": 2,
  "separator": " · ",
  "bar_style": "dots",
  "bold": false,
  "show_git": true,
  "show_model": true,
  "show_context": true,
  "show_quota": true,
  "show_permissions": true,
  "show_agent_state": true,
  "show_session": true,
  "show_herdr": true,
  "use_icons": true,
  "context_warning_threshold": 75.0,
  "quota_warning_threshold": 20.0
}
```

### Options Reference

| Key | Default | Description |
| :--- | :--- | :--- |
| `theme` | `"default"` | Color theme: `"default"`, `"pastel"`, `"nord"`, `"solarized"`, `"monochrome"` |
| `bar_style` | `"dots"` | Context bar style: `"dots"` (`●○`), `"squares"` (`■□`), `"mini"` (`▄─`), `"solid"` (`█─`) |
| `bold` | `false` | Enable or disable bold font weight (`true` / `false`) |
| `separator` | `" · "` | Separator between blocks |
| `layout` | `"auto"` | `"auto"`, `"wide"`, `"medium"`, or `"compact"` |
| `max_lines` | `2` | Maximum statusline lines (1, 2, or 3) |
| `show_git` | `true` | Show Git branch and dirty status |
| `show_herdr` | `true` | Show Herdr active pane ID |
| `context_warning_threshold` | `75.0` | Alert threshold (%) when context window usage is high |
| `quota_warning_threshold` | `20.0` | Alert threshold (%) when remaining quota is low |

---

## 🧪 Testing & Verification

Run the built-in test suite:
```bash
python3 ~/.config/agy-statusline/tests/test_statusline.py
```

Run a live demo preview:
```bash
python3 ~/.config/agy-statusline/statusline.py --demo
```

---

## 🗑️ Uninstallation

To restore AGY CLI to default statusline:
```bash
bash ~/.config/agy-statusline/uninstall.sh
```

---

## 📄 License

This project is open-source under the [MIT License](LICENSE).
