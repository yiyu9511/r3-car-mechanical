#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
从芯路城 pcbdoc 直接生成 F407 Mini 板的外形/孔位三件套：
  1) docs/ref/F407mini_孔位预览.png      —— 带标注的俯视图，屏幕上看
  2) docs/ref/F407mini_1比1打印复核.pdf  —— 1:1 打印，把板子放上去核对
  3) parts/F407mini_外形孔位.dxf         —— 导入 FreeCAD → Pad 1.6mm → 即得实体（可再导出 STEP）

数据来源：f407/materials/STM32F407VET6-Mini开发板封装/*.pcbdoc（Altium ASCII）
所有坐标都从该文件现场解析，不写死，改文件即改结果。
"""

import math
import os
import re
from pathlib import Path

from PIL import Image, ImageDraw

PCBDOC = Path(r"E:\car_projects\f407\materials\STM32F407VET6-Mini开发板封装"
              r"\STM32F407VET6-Mini开发板封装.pcbdoc")
OUT_REF = Path(r"E:\car_projects\freecad\docs\ref")
OUT_PARTS = Path(r"E:\car_projects\freecad\parts")


def mil2mm(v):
    m = re.match(r"([-\d.]+)mil", v or "")
    return round(float(m.group(1)) * 0.0254, 4) if m else None


def parse():
    text = PCBDOC.read_text(encoding="ascii", errors="replace")
    recs = [r for r in text.split("|RECORD=") if r.strip()]
    pad_records, outline_tracks, arcs = [], [], []
    for r in recs:
        fields = {}
        for f in r.split("|"):
            if "=" in f:
                k, v = f.split("=", 1)
                fields[k] = v
        head = r.split("|", 1)[0]
        if head.startswith("Pad"):
            pad_records.append(fields)
        elif head.startswith("Track") and fields.get("LAYER") == "TOPOVERLAY":
            outline_tracks.append(fields)
        elif head.startswith("Arc"):
            arcs.append(fields)
    return pad_records, outline_tracks, arcs


def geometry(pads, tracks, arcs):
    # 板框：取 TOPOVERLAY 上四条长边（>20mm 的就是边框线）
    xs_all, ys_all = [], []
    for t in tracks:
        p = [mil2mm(t.get("X1")), mil2mm(t.get("Y1")), mil2mm(t.get("X2")), mil2mm(t.get("Y2"))]
        if None in p:
            continue
        if math.hypot(p[2] - p[0], p[3] - p[1]) > 20:
            xs_all += [p[0], p[2]]
            ys_all += [p[1], p[3]]
    x0, x1, y0, y1 = min(xs_all), max(xs_all), min(ys_all), max(ys_all)
    radius = mil2mm(arcs[0].get("RADIUS")) if arcs else 3.053

    holes, pins = [], []
    for p in pads:
        x, y, hd = mil2mm(p.get("X")), mil2mm(p.get("Y")), mil2mm(p.get("HOLESIZE"))
        if x is None or y is None or hd is None:
            continue
        (holes if hd > 2.0 else pins).append((x, y, hd))

    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    board = dict(x0=x0, x1=x1, y0=y0, y1=y1, r=radius, cx=cx, cy=cy,
                 w=x1 - x0, h=y1 - y0)
    holes_l = [(x - cx, y - cy, d) for x, y, d in holes]
    pins_l = [(x - cx, y - cy, d) for x, y, d in pins]
    return board, holes_l, pins_l


def draw_png(board, holes, pins, path, png_scale=8):
    W, H = board["w"], board["h"]
    m = 70  # 标注留白
    M = 9   # 像素/毫米
    px = lambda v: int(v * M)
    img = Image.new("RGB", (px(W) + m * 2, px(H) + m * 2), "white")
    d = ImageDraw.Draw(img)
    ox, oy = m, m

    def P(x, y):
        return (ox + px(x + W / 2), oy + px(H / 2 - y))  # 板中心为原点，y 向上

    # 板框（圆角）：P() 里 y 向上，故左上角是 (x0, y0+H)、右下角是 (x0+W, y0)
    x0, y0 = -W / 2, -H / 2
    tl, br = P(x0, y0 + H), P(x0 + W, y0)
    d.rounded_rectangle([tl[0], tl[1], br[0], br[1]],
                        radius=px(board["r"]), outline="black", width=2)

    def circle(x, y, dia, fill, outline):
        r = px(dia / 2)
        cx, cy = P(x, y)
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=fill, outline=outline)

    for x, y, dia in pins:
        circle(x, y, min(dia, 0.9), "#d8d8d8", "#909090")
    for x, y, dia in holes:
        circle(x, y, dia, "#ff9c9c", "#c03030")
        circle(x, y, dia + 1.7, None, "#e0a0a0")  # 焊盘示意

    # 标注
    d.text((ox + px(W) / 2 - 22, oy + px(H) + 18), f"{W:.2f} mm  (board width)", fill="black")
    d.text((ox + px(W) + 8, oy + px(H) / 2 - 20), f"{H:.2f} mm", fill="black")
    hs = sorted({round(abs(x), 3) for x, _, _ in holes})
    d.text((ox + 4, oy + px(H) + 34),
           f"holes: {len(holes)} x dia {holes[0][2]:.2f}   "
           f"pitch X {2*max(hs):.2f}  Y {2*max(abs(y) for _, y, _ in holes):.2f}", fill="#c03030")
    d.text((ox + 4, oy + px(H) + 48), f"pins: {len(pins)} x dia 0.90  (headers 2x22 each side)",
           fill="#555555")
    d.text((ox + 4, 8), "F407VET6 Mini - from Xinlucity pcbdoc (TOP view)", fill="black")
    img.save(path, "PNG")
    return img.size


def draw_1to1_pdf(board, holes, pins, path, dpi=300):
    """1:1 图纸：按 300dpi 出图，打印时不缩放即为真实尺寸。"""
    mm2px = dpi / 25.4
    W, H = board["w"], board["h"]
    pad = 20  # 边距 mm
    img = Image.new("RGB", (int((W + pad * 2) * mm2px), int((H + pad * 2) * mm2px)), "white")
    d = ImageDraw.Draw(img)
    ox = oy = pad * mm2px

    def P(x, y):
        return (ox + (x + W / 2) * mm2px, oy + (H / 2 - y) * mm2px)

    tl, br = P(-W / 2, H / 2), P(W / 2, -H / 2)
    d.rounded_rectangle([tl[0], tl[1], br[0], br[1]],
                        radius=board["r"] * mm2px, outline="black", width=3)
    for x, y, dia in pins:
        r = dia / 2 * mm2px
        cx, cy = P(x, y)
        d.ellipse([cx - r, cy - r, cx + r, cy + r], outline="#808080", width=1)
    for x, y, dia in holes:
        r = dia / 2 * mm2px
        cx, cy = P(x, y)
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill="#ff7b7b", outline="#a02020", width=2)
    d.text((ox, 6), "1:1  check print  -  F407VET6 Mini  (print at 100%, no scaling)", fill="black")
    img.save(path, "PDF", resolution=dpi)
    return img.size


def write_dxf(board, holes, pins, path):
    W, H, r = board["w"], board["h"], board["r"]
    x0, y0 = -W / 2, -H / 2
    x1, y1 = W / 2, H / 2
    bulge = math.tan(math.pi / 8)  # 90° 圆弧
    verts = [
        (x0 + r, y0, 0.0), (x1 - r, y0, bulge), (x1, y0 + r, 0.0), (x1, y1 - r, bulge),
        (x1 - r, y1, 0.0), (x0 + r, y1, bulge), (x0, y1 - r, 0.0), (x0, y0 + r, bulge),
    ]
    out = ["0", "SECTION", "2", "HEADER", "9", "$ACADVER", "1", "AC1015",
           "9", "$INSUNITS", "70", "4", "0", "ENDSEC",
           "0", "SECTION", "2", "ENTITIES"]
    # 板外形
    out += ["0", "LWPOLYLINE", "8", "OUTLINE", "100", "AcDbEntity", "100", "AcDbPolyline",
            "90", str(len(verts)), "70", "1"]
    for vx, vy, b in verts:
        out += ["10", f"{vx:.4f}", "20", f"{vy:.4f}", "42", f"{b:.6f}"]
    # 固定孔
    for x, y, dia in holes:
        out += ["0", "CIRCLE", "8", "HOLE", "10", f"{x:.4f}", "20", f"{y:.4f}",
                "30", "0.0", "40", f"{dia/2:.4f}"]
    # 排针孔
    for x, y, dia in pins:
        out += ["0", "CIRCLE", "8", "PIN", "10", f"{x:.4f}", "20", f"{y:.4f}",
                "30", "0.0", "40", f"{dia/2:.4f}"]
    out += ["0", "ENDSEC", "0", "EOF"]
    path.write_text("\n".join(out), encoding="ascii")


if __name__ == "__main__":
    pads, tracks, arcs = parse()
    board, holes, pins = geometry(pads, tracks, arcs)
    print(f"板外形: {board['w']:.3f} x {board['h']:.3f} mm  圆角 R{board['r']:.3f}")
    print(f"安装孔 {len(holes)} 个 Ø{holes[0][2]}  "
          f"孔距 X={2*max(abs(x) for x,_,_ in holes):.3f} Y={2*max(abs(y) for _,y,_ in holes):.3f}")
    print(f"排针孔 {len(pins)} 个")
    OUT_REF.mkdir(parents=True, exist_ok=True)
    OUT_PARTS.mkdir(parents=True, exist_ok=True)
    print("PNG:", draw_png(board, holes, pins, OUT_REF / "F407mini_孔位预览.png"))
    print("PDF:", draw_1to1_pdf(board, holes, pins, OUT_REF / "F407mini_1比1打印复核.pdf"))
    write_dxf(board, holes, pins, OUT_PARTS / "F407mini_外形孔位.dxf")
    print("DXF:", OUT_PARTS / "F407mini_外形孔位.dxf")
