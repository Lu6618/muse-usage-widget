#!/usr/bin/env python3
"""按 scriptable-widget-multi.js 的版式，用真实 JSON 画 Medium 预览图。
版式：顶栏 + 每服务一行（名 + 条 + 剩余% + 重置/原因）+ 底栏。"""
import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

BASE = Path(__file__).resolve().parent.parent
data = json.loads((BASE / "data" / "ai_usage.json").read_text(encoding="utf-8"))

S = 3
W, H = 364 * S, 170 * S
BG = (251, 246, 236)
TITLE = (36, 26, 18)
LABEL = (138, 122, 102)
TRACK = (233, 223, 201)
FOOT = (160, 139, 116)
GREY = (154, 141, 122)
RED = (220, 38, 38)
YELLOW = (217, 119, 6)
GREEN = (22, 163, 74)


def font(size, bold=False):
    for p in ["/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc" if bold else
              "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
              "/usr/share/fonts/opentype/noto/NotoSerifCJK-Regular.ttc"]:
        try:
            return ImageFont.truetype(p, size)
        except Exception:
            continue
    return ImageFont.load_default()


def remain_color(rem):
    if rem <= 10:
        return RED
    if rem <= 25:
        return YELLOW
    return GREEN


img = Image.new("RGB", (W, H), BG)
d = ImageDraw.Draw(img)
x0, x1 = 14 * S, W - 14 * S
y = 10 * S
d.text((x0, y), "AI 用量", fill=TITLE, font=font(16 * S, True))
upd = data["updated_at"][5:10].replace("-", "/") + " " + data["updated_at"][11:16]
tw = d.textlength(upd, font=font(11 * S))
d.text((x1 - tw, y + 2 * S), upd, fill=LABEL, font=font(11 * S))
y += 26 * S
for s in data["services"]:
    bx = x0
    d.text((bx, y), s["name"], fill=TITLE, font=font(12 * S, True))
    nw = d.textlength(s["name"], font=font(12 * S, True))
    bar_x = bx + nw + 6 * S
    by = y + 5 * S
    d.rounded_rectangle([bar_x, by, bar_x + 84 * S, by + 6 * S], radius=3 * S, fill=TRACK)
    px = bar_x + 90 * S
    if s["status"] == "ok":
        rem = s["percent_remaining"]
        fw = max(84 * S * rem // 100, 4 * S if rem > 0 else 0)
        if fw:
            d.rounded_rectangle([bar_x, by, bar_x + fw, by + 6 * S], radius=3 * S, fill=remain_color(rem))
        t = f"剩{rem}%"
        d.text((px, y), t, fill=remain_color(rem), font=font(12 * S, True))
        sub = f"{s['resets_at'][5:7].lstrip('0')}-{s['resets_at'][8:10]} {s['resets_at'][11:16]}·剩{s['days_left']}天"
        sx = px + d.textlength(t, font=font(12 * S, True)) + 6 * S
        d.text((sx, y + 1 * S), sub, fill=LABEL, font=font(10 * S))
    else:
        t = "查不到"
        d.text((px, y), t, fill=GREY, font=font(12 * S, True))
        sx = px + d.textlength(t, font=font(12 * S, True)) + 6 * S
        d.text((sx, y + 1 * S), s.get("short", ""), fill=LABEL, font=font(10 * S))
    y += 26 * S
fy = H - 20 * S
d.text((x0, fy), "iOS 定时刷新 · 非实时", fill=FOOT, font=font(10 * S))
t = "额外 30B"
tw = d.textlength(t, font=font(10 * S))
d.text((x1 - tw, fy), t, fill=FOOT, font=font(10 * S))

out = BASE / "preview-multi.png"
img.save(out)
print(out, img.size)
