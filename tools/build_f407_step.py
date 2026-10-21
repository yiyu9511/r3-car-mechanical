# -*- coding: utf-8 -*-
# 从 F407mini_外形孔位.dxf（嘉立创导出：OUTLINE/HOLE/PIN 三层）生成 F407 Mini 开发板 STEP
# 外形：圆角矩形 40.894×68.59（圆角 r3.053，圆心即 4 个安装孔位 ±17.394/±31.242）
# 安装孔 4×Ø3.2；排针孔 Ø0.9（PIN 层，2×11，2.54 间距）
# 用法: freecadcmd.exe build_f407_step.py
import sys

LOG = r"E:/car_projects/freecad/output/build_f407_step_report.txt"
def w(s):
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(s + "\n")
    sys.stdout.write(s + "\n"); sys.stdout.flush()
open(LOG, "w").close()

import FreeCAD as App
from FreeCAD import Base
import Part, Import

# ---- 从 DXF 实测值（文本解析核对过） ----
HX, HY = 20.4470, 34.2953          # 板半宽/半长（直边）
CR = 3.053                          # 圆角半径（= 20.447-17.394）
HOLE_X, HOLE_Y, HOLE_R = 17.3937, 31.2420, 1.6   # 4×Ø3.2 安装孔
PIN_R = 0.45                        # 排针孔 Ø0.9
PINS = []  # 从 DXF 读出的 PIN 圆（2×11）
import re
txt = open(r"E:/car_projects/freecad/parts/F407mini_外形孔位.dxf", encoding="ascii", errors="ignore").read()
# 粗解析：CIRCLE 实体，layer PIN：... 8\nPIN\n 10\nx 20\ny 40\nr
for m in re.finditer(r"CIRCLE\n8\nPIN\n(?:100\n[^\n]+\n)*?10\n([-\d.]+)\n20\n([-\d.]+)\n(?:30\n[-\d.]+\n)?40\n([-\d.]+)", txt):
    PINS.append((float(m.group(1)), float(m.group(2)), float(m.group(3))))
w("PIN 孔数量: %d" % len(PINS))

doc = App.newDocument("f407mini")

# 板体：盒 + 四角竖边倒圆
board = Part.makeBox(2*HX, 2*HY, 1.6, Base.Vector(-HX, -HY, 0))
fillets = [e for e in board.Edges if abs(e.Length - 1.6) < 0.01]  # 4 条竖边
board = board.makeFillet(CR, fillets)

# 安装孔 4×Ø3.2
for sx in (-1, 1):
    for sy in (-1, 1):
        c = Part.makeCylinder(HOLE_R, 3, Base.Vector(sx*HOLE_X, sy*HOLE_Y, -0.5))
        board = board.cut(c)
# 排针孔 Ø0.9
for px, py, pr in PINS:
    c = Part.makeCylinder(pr, 3, Base.Vector(px, py, -0.5))
    board = board.cut(c)
board = board.removeSplitter()

obj = doc.addObject("Part::Feature", "F407Mini_PCB")
obj.Shape = board
obj.Label = "F407Mini开发板_外形孔位"

out = r"E:/car_projects/freecad/models/F407Mini开发板_外形孔位.step"
Import.export([obj], out)

bb = board.BoundBox
w("bbox: X[%.3f,%.3f] Y[%.3f,%.3f] Z[%.2f,%.2f]" % (bb.XMin, bb.XMax, bb.YMin, bb.YMax, bb.ZMin, bb.ZMax))
w("体积 %.1f mm^3" % board.Volume)
w("已导出: %s" % out)

# 验证：重新导入，扫圆柱面
doc2 = App.newDocument("verify")
Import.insert(out, "verify")
found = {}
for o in doc2.Objects:
    if not hasattr(o, "Shape"):
        continue
    for f in o.Shape.Faces:
        if f.Surface.TypeId == "Part::GeomCylinder" and f.Surface.Axis.z > 0.9:
            d = round(2 * f.Surface.Radius, 2)
            found[d] = found.get(d, 0) + 1
w("验证回读孔径分布: %s" % found)
w("DONE")
