# -*- coding: utf-8 -*-
"""把本地站点同步到 finance-monitor 仓库并推送到 GitHub Pages。
用法: python -X utf8 publish.py
同步: 每日热榜/site → hot/ ；抖音账号监测/site（存在时）→ douyin/
"""
import shutil
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

REPO = Path(__file__).resolve().parent
TOOLS = REPO.parent
# C 盘桥接镜像（2026-11-26 起本机 E/D 盘上的仓库执行 git push 会报
# "not a git repository"——经排查为环境级问题，推送统一走 C 盘裸镜像中转）
MIRROR = Path.home() / "AppData" / "Local" / "hermes" / ".fmpush"
ORIGIN_URL = "https://github.com/umamor/finance-monitor.git"


def sync(src: Path, dst: Path) -> bool:
    if not src.exists():
        print(f"[跳过] {src} 不存在")
        return False
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(src, dst)
    print(f"[同步] {src} → {dst.relative_to(REPO)}")
    return True


def run(*args) -> int:
    r = subprocess.run(args, cwd=str(REPO), capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    out = (r.stdout or "").strip()
    if out:
        print(out)
    err = (r.stderr or "").strip()
    if r.returncode != 0 and err:
        print(err)
    return r.returncode


def _git(cwd: Path, *args) -> int:
    r = subprocess.run(("git",) + args, cwd=str(cwd), capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    out = (r.stdout or "").strip()
    if out:
        print(out)
    err = (r.stderr or "").strip()
    if r.returncode != 0 and err:
        print(err)
    return r.returncode


def ensure_mirror() -> bool:
    if (MIRROR / "HEAD").exists():
        return True
    print(f"[桥接] 镜像不存在，创建：{MIRROR}")
    try:
        MIRROR.parent.mkdir(parents=True, exist_ok=True)
    except Exception:
        pass
    if _git(MIRROR.parent, "clone", "--bare", str(REPO), str(MIRROR)) != 0:
        return False
    _git(MIRROR, "remote", "set-url", "origin", ORIGIN_URL)
    return True


def push_retry(n=3) -> bool:
    """经 C 盘镜像推送（本机 E/D 盘仓库直接 push 异常；镜像桥接已验证）"""
    if not ensure_mirror():
        print("[失败] 桥接镜像不可用")
        return False
    for i in range(n):
        _git(MIRROR, "fetch", str(REPO), "+refs/heads/main:refs/remotes/src/main")
        if _git(MIRROR, "push", "origin", "refs/remotes/src/main:refs/heads/main") == 0:
            return True
        if i < n - 1:
            wait = 10 * (i + 1)
            print(f"[重试] push 失败，{wait}s 后第 {i + 2}/{n} 次…")
            time.sleep(wait)
    return False


def main():
    sync(TOOLS / "每日热榜" / "site", REPO / "hot")
    sync(TOOLS / "抖音账号监测" / "site", REPO / "douyin")
    run("git", "add", "-A")
    if run("git", "commit", "-m", f"站点更新 {datetime.now():%Y-%m-%d %H:%M}") != 0:
        print("（无新变更）")
    # 无论本轮有无新提交都推送——上一次推送失败时在这里自愈补推
    if push_retry(3):
        print("[完成] 已推送，线上 1-2 分钟生效（CDN 缓存约 5-10 分钟）")
    else:
        print("[失败] 推送失败（已重试 3 次）——线上未更新！")
        sys.exit(1)


if __name__ == "__main__":
    main()
