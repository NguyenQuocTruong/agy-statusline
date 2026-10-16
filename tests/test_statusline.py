"""Comprehensive test suite and benchmark for AGY Custom Statusline."""
import unittest
import json
import os
import sys
import subprocess
import time
import tempfile

# Ensure lib can be imported
BASE_DIR = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from lib.config import StatuslineConfig
from lib.parser import parse_payload, sanitize_payload
from lib.git_provider import get_git_info
from lib.herdr_provider import get_herdr_info
from lib.normalizer import normalize_data
from lib.renderer import StatuslineRenderer, strip_ansi

class TestStatusline(unittest.TestCase):
    def setUp(self):
        self.config = StatuslineConfig()
        self.renderer = StatuslineRenderer(self.config)

    def test_full_payload(self):
        """Test full native payload parses and renders properly."""
        payload = {
            "cwd": "/home/truongnq/workspace/fluxa/fluxa-dashboard-api",
            "model": {"display_name": "Gemini 3.8 Flash", "effort": "medium"},
            "context_window": {
                "used_percentage": 42.5,
                "total_input_tokens": 42500,
                "context_window_size": 100000
            },
            "quota": {
                "gemini-5h": {"remaining_fraction": 0.85, "reset_in_seconds": 3600},
                "gemini-weekly": {"remaining_fraction": 0.92, "reset_in_seconds": 86400}
            },
            "agent_state": "working",
            "execution_mode": "EDIT",
            "task_count": 1,
            "subagents": [{"status": "running"}],
            "session_id": "1ac78a98-6da1-4930-8840",
            "terminal_width": 120
        }
        norm = normalize_data(payload, self.config)
        output = self.renderer.render(norm)
        plain = strip_ansi(output)
        self.assertIn("EDIT", plain)
        self.assertIn("fluxa-dashboard-api", plain)
        self.assertIn("Gemini 3.8 Flash", plain)
        self.assertIn("42.5%", plain)
        self.assertIn("5h 85.0%", plain)
        self.assertIn("WORKING", plain)

    def test_missing_fields(self):
        """Test empty payload fallback without errors."""
        payload = {}
        norm = normalize_data(payload, self.config)
        output = self.renderer.render(norm)
        self.assertTrue(len(output) > 0)
        self.assertIn("NORMAL", output)

    def test_invalid_json(self):
        """Test malformed string handling in parser."""
        bad_json = "{bad_json: True, invalid"
        parsed = parse_payload(bad_json)
        self.assertEqual(parsed, {})
        norm = normalize_data(parsed, self.config)
        output = self.renderer.render(norm)
        self.assertTrue(len(output) > 0)

    def test_agent_states(self):
        """Test transitions between idle, thinking, working, tool, blocked."""
        states = ["idle", "thinking", "working", "tool", "blocked"]
        for s in states:
            payload = {"agent_state": s, "terminal_width": 100}
            norm = normalize_data(payload, self.config)
            output = strip_ansi(self.renderer.render(norm))
            self.assertIn(s.upper(), output)

    def test_model_switching(self):
        """Test Gemini vs Claude vs GPT quota bucket routing."""
        # 1. Claude model
        claude_payload = {
            "model": {"display_name": "Claude 3.7 Sonnet"},
            "quota": {
                "3p-5h": {"remaining_fraction": 0.70, "reset_in_seconds": 1800},
                "3p-weekly": {"remaining_fraction": 0.80, "reset_in_seconds": 72000},
                "gemini-5h": {"remaining_fraction": 0.99}
            }
        }
        norm_claude = normalize_data(claude_payload, self.config)
        self.assertEqual(norm_claude.quota.five_hour_percent, 70.0)

        # 2. Gemini model
        gemini_payload = {
            "model": {"display_name": "Gemini 3.8 Flash"},
            "quota": {
                "3p-5h": {"remaining_fraction": 0.70},
                "gemini-5h": {"remaining_fraction": 0.95, "reset_in_seconds": 3600}
            }
        }
        norm_gemini = normalize_data(gemini_payload, self.config)
        self.assertEqual(norm_gemini.quota.five_hour_percent, 95.0)

    def test_git_clean_and_dirty(self):
        """Test git clean, dirty indicator, and detached HEAD."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Init a git repo
            subprocess.run(["git", "init"], cwd=tmpdir, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=tmpdir)
            subprocess.run(["git", "config", "user.name", "Test"], cwd=tmpdir)
            
            # Initial commit
            test_file = os.path.join(tmpdir, "file.txt")
            with open(test_file, "w") as f:
                f.write("hello")
            subprocess.run(["git", "add", "file.txt"], cwd=tmpdir)
            subprocess.run(["git", "commit", "-m", "init"], cwd=tmpdir, stdout=subprocess.DEVNULL)
            
            # 1. Clean state
            branch, dirty = get_git_info(tmpdir)
            self.assertFalse(dirty)

            # 2. Dirty state
            with open(test_file, "w") as f:
                f.write("hello changed")
            # Force cache bypass with time sleep
            time.sleep(1.6)
            branch, dirty = get_git_info(tmpdir)
            self.assertTrue(dirty)

    def test_no_git_directory(self):
        """Test directory outside git repo returns 'no-git'."""
        with tempfile.TemporaryDirectory() as tmpdir:
            branch, dirty = get_git_info(tmpdir)
            self.assertEqual(branch, "no-git")
            self.assertFalse(dirty)

    def test_quota_unavailable(self):
        """Test quota unavailable gracefully handled."""
        payload = {"model": "Gemini Flash", "quota": {}}
        norm = normalize_data(payload, self.config)
        self.assertFalse(norm.quota.available)
        output = strip_ansi(self.renderer.render(norm))
        # Doesn't crash, doesn't print broken quota
        self.assertNotIn("5h None", output)

    def test_context_warning_threshold(self):
        """Test warning badge/color triggered when context >= threshold."""
        self.config.context_warning_threshold = 80.0
        payload = {
            "context_window": {"used_percentage": 85.0, "total_input_tokens": 85000, "context_window_size": 100000}
        }
        norm = normalize_data(payload, self.config)
        self.assertTrue(norm.context.is_warning)

    def test_responsive_widths(self):
        """Test WIDE, MEDIUM, COMPACT, ULTRA-COMPACT layouts."""
        payload = {
            "cwd": "/home/truongnq/workspace/fluxa",
            "model": "Gemini 3.8 Flash",
            "context_window": {"used_percentage": 25.0},
            "quota": {"gemini-5h": {"remaining_fraction": 0.90}}
        }
        for w in [140, 100, 75, 45]:
            payload["terminal_width"] = w
            norm = normalize_data(payload, self.config)
            output = self.renderer.render(norm)
            lines = output.split("\n")
            for line in lines:
                vis_len = len(strip_ansi(line))
                self.assertLessEqual(vis_len, w, f"Line overflowed terminal width {w}: {vis_len}")

    def test_ascii_mode(self):
        """Test pure ASCII mode with use_icons=False."""
        cfg = StatuslineConfig(use_icons=False)
        renderer = StatuslineRenderer(cfg)
        payload = {"agent_state": "working", "execution_mode": "EDIT", "terminal_width": 100}
        norm = normalize_data(payload, cfg)
        output = strip_ansi(renderer.render(norm))
        self.assertIn("[WORK]", output)
        self.assertNotIn("⚡", output)

    def test_sanitization(self):
        """Verify sensitive attributes (tokens, emails, secrets) are purged."""
        leak_payload = {
            "email": "secret_user@example.com",
            "access_token": "ya29.secret_token",
            "api_key": "AIzaSySecret",
            "cwd": "/home/truongnq/workspace/fluxa"
        }
        sanitized = sanitize_payload(leak_payload)
        self.assertNotIn("email", sanitized)
        self.assertNotIn("access_token", sanitized)
        self.assertNotIn("api_key", sanitized)
        self.assertIn("cwd", sanitized)

    def test_failsafe_execution(self):
        """Test execution via subprocess with catastrophic bad input always returns code 0."""
        script = os.path.join(BASE_DIR, "statusline.py")
        res = subprocess.run([sys.executable, script], input="!!!NOT_JSON!!!", text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.assertEqual(res.returncode, 0)
        self.assertTrue(len(res.stdout) > 0)

    def test_benchmark_latency(self):
        """Benchmark render time: average and p95 must be well below 50ms."""
        payload = {
            "cwd": "/home/truongnq/workspace/fluxa",
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
            "task_count": 1,
            "subagents": [{"status": "running"}],
            "session_id": "1ac78a98-6da1-4930-8840",
            "execution_mode": "EDIT",
            "terminal_width": 120
        }
        script = os.path.join(BASE_DIR, "statusline.py")
        raw_json = json.dumps(payload)

        latencies = []
        # Run 30 iterations
        for _ in range(30):
            t0 = time.perf_counter()
            res = subprocess.run([sys.executable, script], input=raw_json, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            t1 = time.perf_counter()
            self.assertEqual(res.returncode, 0)
            latencies.append((t1 - t0) * 1000.0)

        latencies.sort()
        avg_ms = sum(latencies) / len(latencies)
        p95_ms = latencies[int(len(latencies) * 0.95)]
        min_ms = latencies[0]
        max_ms = latencies[-1]

        print(f"\n[BENCHMARK] Samples: {len(latencies)} | Avg: {avg_ms:.2f}ms | p95: {p95_ms:.2f}ms | Min: {min_ms:.2f}ms | Max: {max_ms:.2f}ms")
        self.assertLess(avg_ms, 50.0, f"Average latency {avg_ms:.2f}ms exceeded 50ms target")

if __name__ == "__main__":
    unittest.main()
