#!/usr/bin/env python3
"""
Custom Statusline for AGY CLI (Google Antigravity CLI).
Renders real-time telemetry, model, context, quota, git, execution mode, permissions, and agent state.
"""
import sys
import os

# Add root directory to sys.path so lib package can be imported
SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

from lib.config import StatuslineConfig
from lib.parser import parse_payload
from lib.normalizer import normalize_data
from lib.renderer import StatuslineRenderer

def main():
    try:
        # Load configuration
        config = StatuslineConfig.load()
        renderer = StatuslineRenderer(config)

        # Handle command-line arguments for testing/demo
        if len(sys.argv) > 1:
            arg = sys.argv[1]
            if arg in ("--help", "-h"):
                print("Usage: statusline.py [--demo | --test]")
                sys.exit(0)
            elif arg == "--demo":
                demo_payload = {
                    "cwd": os.getcwd(),
                    "model": {"display_name": "Gemini 3.8 Flash (Medium)", "effort": "medium"},
                    "context_window": {
                        "used_percentage": 11.4,
                        "total_input_tokens": 25000,
                        "context_window_size": 218000
                    },
                    "quota": {
                        "gemini-5h": {"remaining_fraction": 0.86, "reset_in_seconds": 7200},
                        "gemini-weekly": {"remaining_fraction": 0.78, "reset_in_seconds": 432000}
                    },
                    "agent_state": "working",
                    "task_count": 0,
                    "subagents": [{"status": "running"}, {"status": "running"}],
                    "session_id": "1ac78a98-6da1-4930-8840",
                    "execution_mode": "EDIT",
                    "terminal_width": 120
                }
                norm = normalize_data(demo_payload, config)
                print(renderer.render(norm))
                sys.exit(0)

        # Standard execution: parse JSON from stdin
        payload = parse_payload()
        norm = normalize_data(payload, config)
        rendered = renderer.render(norm)
        sys.stdout.write(rendered + "\n")
        sys.stdout.flush()

    except Exception:
        # Failsafe: Never crash or exit non-zero so AGY never auto-disables statusline
        try:
            cwd_base = os.path.basename(os.getcwd()) or "fluxa"
            sys.stdout.write(f"⚡ AGY · 📁 {cwd_base}\n")
            sys.stdout.flush()
        except Exception:
            pass
        sys.exit(0)

if __name__ == "__main__":
    main()
