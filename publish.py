# -*- coding: utf-8 -*-
"""把本地站点同步到 finance-monitor 仓库并推送到 GitHub Pages。
用法: python -X utf8 publish.py
同步: 每日热榜/site → hot/ ；抖音账号监测/site（存在时）→ douyin/
"""
import shutil
import subprocess
from datetime import datetime
from pathlib import Path

REPO = Path(__file__).resolve().parent
TOOLS = REPO.parent


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


def main():
    sync(TOOLS / "每日热榜" / "site", REPO / "hot")
    sync(TOOLS / "抖音账号监测" / "site", REPO / "douyin")
    run("git", "add", "-A")
    if run("git", "commit", "-m", f"站点更新 {datetime.now():%Y-%m-%d %H:%M}") != 0:
        print("（无变更，跳过推送）")
        return
    if run("git", "push") == 0:
        print("[完成] 已推送，线上 1-2 分钟生效（CDN 缓存约 5-10 分钟）")
    else:
        print("[失败] 推送失败")


if __name__ == "__main__":
    main()
