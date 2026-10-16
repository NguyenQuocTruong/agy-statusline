"""Ultra-fast Git metadata provider using direct filesystem reads and smart caching."""
import os
import subprocess
import time
from typing import Tuple, Optional, Dict, Any

# Fast in-memory cache: cwd -> (timestamp, branch, is_dirty)
_CACHE: Dict[str, Tuple[float, str, bool]] = {}
CACHE_TTL = 1.0  # seconds

def find_git_dir(start_dir: str) -> Optional[str]:
    """Finds .git directory or worktree file by walking up parents (max 5 levels)."""
    curr = os.path.abspath(start_dir)
    for _ in range(5):
        git_path = os.path.join(curr, ".git")
        if os.path.exists(git_path):
            if os.path.isdir(git_path):
                return git_path
            elif os.path.isfile(git_path):
                try:
                    with open(git_path, "r", encoding="utf-8") as f:
                        line = f.readline().strip()
                    if line.startswith("gitdir:"):
                        target = line[7:].strip()
                        if not os.path.isabs(target):
                            target = os.path.normpath(os.path.join(curr, target))
                        return target
                except Exception:
                    pass
                return git_path
        parent = os.path.dirname(curr)
        if parent == curr:
            break
        curr = parent
    return None

def get_git_info(cwd: Optional[str] = None, payload_vcs: Optional[Dict[str, Any]] = None) -> Tuple[str, bool]:
    """
    Returns (branch, is_dirty).
    1. Uses native payload VCS if present.
    2. Uses direct .git/HEAD file reading (0.05ms).
    3. Runs fast git status with 1s caching.
    """
    # 1. Check native payload VCS first
    if payload_vcs and isinstance(payload_vcs, dict):
        branch = payload_vcs.get("branch")
        dirty = bool(payload_vcs.get("dirty", False))
        if branch:
            return str(branch), dirty

    if not cwd or not os.path.isdir(cwd):
        return "no-git", False

    cwd = os.path.abspath(cwd)
    now = time.time()

    # 2. Check memory cache
    if cwd in _CACHE:
        cached_time, cached_branch, cached_dirty = _CACHE[cwd]
        if now - cached_time < CACHE_TTL:
            return cached_branch, cached_dirty

    # 3. Locate .git
    git_dir = find_git_dir(cwd)
    if not git_dir:
        _CACHE[cwd] = (now, "no-git", False)
        return "no-git", False

    # 4. Read .git/HEAD directly (extremely fast: 0.05ms)
    head_file = os.path.join(git_dir, "HEAD")
    branch = "unknown"
    if os.path.isfile(head_file):
        try:
            with open(head_file, "r", encoding="utf-8") as f:
                head_content = f.read().strip()
            if head_content.startswith("ref: refs/heads/"):
                branch = head_content[16:]
            elif len(head_content) >= 7:
                # Detached HEAD (commit hash)
                branch = head_content[:7]
        except Exception:
            branch = "unknown"

    # 5. Quick git status check (handles both staged and unstaged edits)
    is_dirty = False
    try:
        status_res = subprocess.run(
            ["git", "-C", cwd, "status", "--porcelain", "-uno"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=0.04
        )
        is_dirty = bool(status_res.stdout.strip())
    except Exception:
        is_dirty = False

    _CACHE[cwd] = (now, branch, is_dirty)
    return branch, is_dirty
