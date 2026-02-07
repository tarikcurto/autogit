#!/usr/bin/env python3
import argparse
import json
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple


@dataclass
class RepoCfg:
    path: Path
    remote: str = "origin"
    branch: str = "main"
    message: str = "Auto-commit {timestamp}"
    excludes: List[str] = None


@dataclass
class GlobalCfg:
    pull_rebase: bool = True
    push: bool = True
    commit_if_no_changes: bool = False  # normally False


def run_capture(cmd: List[str], cwd: Path) -> Tuple[int, str]:
    p = subprocess.run(
        cmd,
        cwd=str(cwd),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    return p.returncode, p.stdout


def run_check(cmd: List[str], cwd: Path) -> None:
    rc, out = run_capture(cmd, cwd)
    if rc != 0:
        raise RuntimeError(f"Command failed ({rc}): {' '.join(cmd)}\n{out}")


def is_git_repo(path: Path) -> bool:
    return (path / ".git").exists()


def git_has_changes(repo: Path) -> bool:
    rc, out = run_capture(["git", "status", "--porcelain"], repo)
    if rc != 0:
        raise RuntimeError(f"git status failed in {repo}:\n{out}")
    return out.strip() != ""


def git_has_staged_changes(repo: Path) -> bool:
    rc, out = run_capture(["git", "diff", "--cached", "--quiet"], repo)
    # rc = 0 => no staged changes
    # rc = 1 => staged changes exist
    # rc >1 => error
    if rc == 0:
        return False
    if rc == 1:
        return True
    raise RuntimeError(f"git diff --cached failed in {repo}:\n{out}")


def build_git_add_cmd(excludes: Optional[List[str]]) -> List[str]:
    # git pathspec magic: :(exclude,glob)pat
    cmd = ["git", "add", "-A", "--", "."]
    for pat in (excludes or []):
        cmd.append(f":(exclude,glob){pat}")
    return cmd


def load_config(cfg_path: Path) -> Tuple[List[RepoCfg], GlobalCfg]:
    with cfg_path.open("r", encoding="utf-8") as f:
        cfg = json.load(f)

    repos_raw = cfg.get("repos", [])
    if not isinstance(repos_raw, list) or not repos_raw:
        raise ValueError("'repos' must be a non-empty list in JSON.")

    global_raw = cfg.get("global", {}) or {}
    global_cfg = GlobalCfg(
        pull_rebase=bool(global_raw.get("pull_rebase", True)),
        push=bool(global_raw.get("push", True)),
        commit_if_no_changes=bool(global_raw.get("commit_if_no_changes", False)),
    )

    repos: List[RepoCfg] = []
    for r in repos_raw:
        if "path" not in r:
            raise ValueError("Each element in 'repos' must have 'path'.")
        repos.append(
            RepoCfg(
                path=Path(r["path"]).expanduser(),
                remote=r.get("remote", "origin"),
                branch=r.get("branch", "main"),
                message=r.get("message", "Auto-commit {timestamp}"),
                excludes=list(r.get("excludes", []) or []),
            )
        )

    return repos, global_cfg


def sync_repo(repo_cfg: RepoCfg, g: GlobalCfg, timestamp: str, dry_run: bool) -> int:
    repo = repo_cfg.path.resolve()
    print(f"\n=== Repo: {repo} ===")

    if not repo.exists():
        print(f"[WARN] Directory does not exist: {repo}")
        return 1
    if not is_git_repo(repo):
        print(f"[WARN] Does not appear to be a git repo (no .git): {repo}")
        return 1

    # Pull (optional)
    if g.pull_rebase:
        fetch_cmd = ["git", "fetch", repo_cfg.remote]
        pull_cmd = ["git", "pull", "--rebase", "--autostash", repo_cfg.remote, repo_cfg.branch]
        if dry_run:
            print(f"[DRY] {' '.join(fetch_cmd)}")
            print(f"[DRY] {' '.join(pull_cmd)}")
        else:
            # fetch non-critical
            run_capture(fetch_cmd, repo)
            rc, out = run_capture(pull_cmd, repo)
            if rc != 0:
                print(f"[WARN] git pull failed. Check for conflicts.\n{out}")
                return 1
            print("[OK] Pull done.")

    # Add with excludes
    add_cmd = build_git_add_cmd(repo_cfg.excludes)
    if dry_run:
        print(f"[DRY] {' '.join(add_cmd)}")
    else:
        rc, out = run_capture(add_cmd, repo)
        if rc != 0:
            print(f"[WARN] git add failed:\n{out}")
            return 1

    # Changes?
    # if not git_has_changes(repo):
    #     if g.commit_if_no_changes:
    #         print("[OK] No changes, but commit_if_no_changes=true (not recommended).")
    #     else:
    #         print("[OK] No changes. Skip.")
    #         return 0
    if git_has_staged_changes(repo):
        print("[OK] Changes detected to commit.")
    else:
        print("[OK] No changes to commit (after applying excludes). Skip.")
        return 0

    # Commit
    msg = repo_cfg.message.replace("{timestamp}", timestamp)
    commit_cmd = ["git", "commit", "-m", msg]

    if dry_run:
        print(f"[DRY] {' '.join(commit_cmd)}")
    else:
        rc, out = run_capture(commit_cmd, repo)
        if rc != 0:
            print(f"[WARN] git commit failed:\n{out}")
            return 1
        print("[OK] Commit done.")

    # Push
    if g.push:
        push_cmd = ["git", "push", repo_cfg.remote, repo_cfg.branch]
        if dry_run:
            print(f"[DRY] {' '.join(push_cmd)}")
        else:
            rc, out = run_capture(push_cmd, repo)
            if rc != 0:
                print(f"[WARN] git push failed:\n{out}")
                return 1
            print("[OK] Push done.")

    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="Auto-commit/push for multiple repos (Obsidian friendly).")
    ap.add_argument("-c", "--config", default="config.json", help="Path to JSON config file (default: config.json)")
    ap.add_argument("--dry-run", action="store_true", help="Does not execute git, only shows what it would do")
    args = ap.parse_args()

    cfg_path = Path(args.config).expanduser()
    if not cfg_path.exists():
        print(f"[ERROR] Config does not exist: {cfg_path}", file=sys.stderr)
        return 2

    try:
        repos, g = load_config(cfg_path)
    except Exception as e:
        print(f"[ERROR] Invalid config: {e}", file=sys.stderr)
        return 2

    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    overall = 0

    for r in repos:
        try:
            rc = sync_repo(r, g, ts, args.dry_run)
            overall = max(overall, rc)
        except Exception as e:
            print(f"[ERROR] Failed in {r.path}: {e}", file=sys.stderr)
            overall = 1

    return overall


if __name__ == "__main__":
    raise SystemExit(main())
