#!/usr/bin/env python3
"""多服务 AI 用量 -> data/ai_usage.json

只取本机能实测到的数，不编数：
- Muse：解析 `subscription-status status`（周限额 + 重置时间 + 额外 tokens）
- Codex：本机有 CLI 0.164 + 登录态，但 ChatGPT/Codex 不提供用量 %
  的 CLI/API，本机取不到 -> status=unavailable
- Claude Code：本机未装 CLI、未登录 -> unavailable
- Grok：CLI 已装 1.0.77 但未配 API Key，App 内用量本机取不到 -> unavailable

用法：python3 scripts/update_ai_usage.py [--out data/ai_usage.json]
输出只含套餐/百分比/重置时间，无账号、无密钥，可放公开 raw。
"""
import argparse
import datetime
import json
import re
import subprocess
import sys
from pathlib import Path

MONTHS = {m: i + 1 for i, m in enumerate(
    ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
     "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"])}

CST = datetime.timezone(datetime.timedelta(hours=8))


def parse_muse(text: str) -> dict:
    plan = "Free"
    if "does not have a subscription" not in text:
        m = re.search(r"(Power|Maximum|Free)[^\n]*", text)
        if m:
            plan = m.group(1)
    used = re.search(r"Usage:\s*(\d+(?:\.\d+)?)%", text)
    percent_used = float(used.group(1)) if used else 0.0
    if float(percent_used).is_integer():
        percent_used = int(percent_used)
    reset_iso = None
    reset_text = None
    m = re.search(
        r"[Rr]esets?\s+([A-Z][a-z]{2})\s+(\d{1,2})\s+at\s+(\d{1,2}):(\d{2})\s*(AM|PM)",
        text)
    if m:
        mon, day, hh, mm, ampm = (MONTHS[m.group(1)], int(m.group(2)),
                                  int(m.group(3)), int(m.group(4)), m.group(5))
        if ampm == "PM" and hh != 12:
            hh += 12
        if ampm == "AM" and hh == 12:
            hh = 0
        now = datetime.datetime.now(CST)
        reset = datetime.datetime(now.year, mon, day, hh, mm, tzinfo=CST)
        if reset < now:
            reset = reset.replace(year=now.year + 1)
        reset_iso = reset.isoformat()
        reset_text = reset.strftime("%m-%d %H:%M")
    extra_used = 0
    extra_left = None
    m = re.search(r"Additional tokens:\s*(\d+(?:\.\d+)?)% used \(([^)]+)\)", text)
    if m:
        extra_used = float(m.group(1))
        if float(extra_used).is_integer():
            extra_used = int(extra_used)
        extra_left = m.group(2).strip()
    days_left = None
    if reset_iso:
        delta = datetime.datetime.fromisoformat(reset_iso) - datetime.datetime.now(CST)
        days_left = max(0, delta.days)
    return {
        "id": "muse",
        "name": "Muse",
        "status": "ok",
        "plan": plan,
        "percent_used": percent_used,
        "percent_remaining": 100 - percent_used,
        "resets_at": reset_iso,
        "resets_at_text": reset_text,
        "days_left": days_left,
        "window_5h": None,
        "extra": {"percent_used": extra_used, "left_label": extra_left},
    }


UNAVAILABLE = [
    {"id": "codex", "name": "Codex", "status": "unavailable",
     "reason": "本机无用量接口，需在 ChatGPT App/网页查", "short": "ChatGPT App 查"},
    {"id": "claude-code", "name": "Claude Code", "status": "unavailable",
     "reason": "本机未安装 CLI、未登录", "short": "未安装/未登录"},
    {"id": "grok", "name": "Grok", "status": "unavailable",
     "reason": "未配 API Key，App 用量本机取不到", "short": "未配 Key"},
]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="data/ai_usage.json")
    args = ap.parse_args()
    try:
        r = subprocess.run(["subscription-status", "status"],
                           capture_output=True, text=True, timeout=60)
    except FileNotFoundError:
        print("subscription-status not found", file=sys.stderr)
        return 1
    if r.returncode != 0:
        print(r.stdout, file=sys.stderr)
        print(r.stderr, file=sys.stderr)
        return 1
    now = datetime.datetime.now(CST)
    out = {
        "updated_at": now.replace(microsecond=0).isoformat(),
        "source": "subscription-status (Muse only)",
        "services": [parse_muse(r.stdout)] + UNAVAILABLE,
    }
    p = Path(args.out)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
