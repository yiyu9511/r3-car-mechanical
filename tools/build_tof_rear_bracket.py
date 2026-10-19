# -*- coding: utf-8 -*-
# TOF后支架 v4 参数化重建（前脸特征全部按 TOFSense_F2 STEP 实测）
# 实测数据（世界系，前脸 y=-125.51）：
#   镜头凸环 Ø6.0 @ (±6.5, z7.5)（中心锥台伸至 y-130.91，±2.05/3.05宽x5高）
#   安装孔 Ø1.0 只有下方 2 个 @ (±5.5, z11.0)——实物确认，模型里 z16 两个是画的
# 旧版错误：所有孔 Z 高 1.5mm，且未给中央锥台留窗
# v4：单一大圆角窗覆盖整个光学区 x±9.7 × z4.1..10.8(世界)，导孔只留下方 2×Ø1.1 @ z11
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
WIN_X, WIN_Z0, WIN_Z1, WIN_R = 9.7, 2.6, 9.3, 2.0   # 大窗（本地 z）
PILOTS = [(-5.5, 9.5), (5.5, 9.5)]  # Ø1.1 只有下方 2 个（世界 z11），实物确认

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
# 导孔 Ø1.1（轴Y，贯通墙）
for px, pz in PILOTS:
    cuts.append(Part.makeCylinder(0.55, 4, Base.Vector(px, -128.7, pz),
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
w("导孔（世界 z）: %s" % [(px, pz+ZW) for px, pz in PILOTS])

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
