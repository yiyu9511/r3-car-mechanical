# -*- coding: utf-8 -*-
# TOF后支架 v4 参数化重建（前脸特征全部按 TOFSense_F2 STEP 实测）
# 实测数据（世界系；STEP 曲线全是 BSpline，靠圆柱面 + 射线探测确认）：
#   前脸是一块平板 y=-125.51（后面还有 0.8mm 间隔的背板 y=-124.71）；
#   Ø6 只是 0.2mm 高的浅环台阶（圆柱面面积仅 3.8mm²），**不是凸台**（射线探测无凸起）
#   安装孔：2×Ø1.6 通孔 @ (±6.5, z7.5)
#   光学凸起：中央 ~7.2×5、伸出 5.4mm 到 y=-130.91（唯一真正凸起的东西）
#   z11/z16 的 4 个 Ø1.0 是 0.1mm 环带，不是孔（旧版据此画错）
# v7：平板墙面无沉台，中央通窗罩光学凸起，2×Ø2.2 过孔拧 M2 自攻
# 本地坐标系：z0 = 底板上表面（世界 z1.5）
# 用法: freecadcmd.exe build_tof_rear_bracket.py
import sys

LOG = r"E:/car_projects/freecad/output/build_tof_v4_report.txt"
def w(s):
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(s + "\n")
    sys.stdout.write(s + "\n"); sys.stdout.flush()
open(LOG, "w").close()

import FreeCAD as App
from FreeCAD import Base
import Part, Mesh

ZW = 1.5  # 本地→世界 z 偏移

# ---------- 参数（本地坐标） ----------
BASE = (-30, -128.5, 0, 60, 18.5, 3)          # x,y,z, dx,dy,dz
WALL = (-12, -128.5, 0, 24, 3, 17)            # 墙 24 宽（窗两侧各留 2.3）
ANCHORS = [(-26, -118.4), (26, -118.4)]       # Ø3.2 锚孔（轴Z）
WIN_X, WIN_Z0, WIN_Z1, WIN_R = 4.0, 3.1, 8.9, 1.2   # 中央通窗（本地 z，世界 4.6..10.4）
SCREWS = [(-6.5, 6.0), (6.5, 6.0)]   # Ø2.2 过孔（本地 z6 = 世界 z7.5），M2 自攻穿墙入模块 Ø1.6 孔

doc = App.newDocument("TOF后支架")

x, y, z, dx, dy, dz = BASE
base = Part.makeBox(dx, dy, dz, Base.Vector(x, y, z))
x, y, z, dx, dy, dz = WALL
wall = Part.makeBox(dx, dy, dz, Base.Vector(x, y, z))
body = base.fuse(wall)

# 大圆角窗 = 横竖两盒 + 四角圆柱
cuts = []
cuts.append(Part.makeBox(2*(WIN_X-WIN_R), 4, WIN_Z1-WIN_Z0,
            Base.Vector(-(WIN_X-WIN_R), -128.7, WIN_Z0)))
cuts.append(Part.makeBox(2*WIN_X, 4, WIN_Z1-WIN_Z0-2*WIN_R,
            Base.Vector(-WIN_X, -128.7, WIN_Z0+WIN_R)))
for sx in (-1, 1):
    for zz in (WIN_Z0+WIN_R, WIN_Z1-WIN_R):
        c = Part.makeCylinder(WIN_R, 4, Base.Vector(sx*(WIN_X-WIN_R), -128.7, zz),
                              Base.Vector(0, 1, 0))
        cuts.append(c)
# M2 自攻过孔 Ø2.2（轴Y，贯通墙）——前脸是平板，不需要任何沉台
for px, pz in SCREWS:
    cuts.append(Part.makeCylinder(1.1, 4, Base.Vector(px, -128.7, pz),
                                  Base.Vector(0, 1, 0)))
# 锚孔 Ø3.2（轴Z，贯通底座）
for ax, ay in ANCHORS:
    cuts.append(Part.makeCylinder(1.6, 5, Base.Vector(ax, ay, -1),
                                  Base.Vector(0, 0, 1)))

for c in cuts:
    body = body.cut(c)
body = body.removeSplitter()

obj = doc.addObject("Part::Feature", "TOF后支架")
obj.Shape = body
doc.saveAs(r"E:/car_projects/freecad/parts/TOF后支架.FCStd")
Mesh.export([obj], r"E:/car_projects/freecad/output/stl/TOF后支架.stl")

bb = body.BoundBox
w("v4 支架 bbox: X[%.1f,%.1f] Y[%.1f,%.1f] Z[%.1f,%.1f]（本地）" % (
    bb.XMin, bb.XMax, bb.YMin, bb.YMax, bb.ZMin, bb.ZMax))
w("大窗（世界）: x±%.1f, z %.1f..%.1f, r%.1f" % (WIN_X, WIN_Z0+ZW, WIN_Z1+ZW, WIN_R))
w("M2 过孔 Ø2.2（世界 z）: %s" % [(px, pz+ZW) for px, pz in SCREWS])

# ---------- 同步更新装配体里的网格 ----------
for asm in [r"E:/car_projects/freecad/test1_B_相机二层.FCStd"]:
    try:
        d = App.openDocument(asm)
        n = 0
        for o in d.Objects:
            if o.TypeId == "Mesh::Feature" and "TOF后支架" in o.Label:
                o.Mesh = Mesh.Mesh(r"E:/car_projects/freecad/output/stl/TOF后支架.stl")
                n += 1
        d.save()
        w("装配体 %s 更新网格 %d 个" % (asm, n))
    except Exception as e:
        w("装配体更新跳过: %s" % e)
w("DONE")
