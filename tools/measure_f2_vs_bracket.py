# -*- coding: utf-8 -*-
# 提取：F2 STEP 前脸所有圆柱面特征（镜头/安装孔）→ 世界坐标；支架现有窗孔位置
# 用法: freecadcmd.exe measure_f2_vs_bracket.py
import sys

LOG = r"E:/car_projects/freecad/output/f2_vs_bracket.txt"
def w(s):
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(s + "\n")
    sys.stdout.write(s + "\n"); sys.stdout.flush()
open(LOG, "w").close()

import FreeCAD as App
from FreeCAD import Base
import Part, Import

# F2 世界变换: (x,y,z) -> (x, -z, y) + (0,-125.5,7.5)
ROT = Base.Matrix(1,0,0,0, 0,0,-1,0, 0,1,0,0, 0,0,0,1)
T = Base.Vector(0, -125.5, 7.5)

def to_world(p):
    q = ROT.multVec(p)
    return Base.Vector(q.x + T.x, q.y + T.y, q.z + T.z)

w("===== F2 STEP 前脸圆柱面（世界坐标）=====")
doc = App.newDocument("m")
Import.insert(r"E:/car_projects/freecad/models/TOFSense_F2_Mini_Appearance_V1.0.step", "m")
seen = set()
for o in doc.Objects:
    if not hasattr(o, "Shape") or len(o.Shape.Faces) == 0:
        continue
    for f in o.Shape.Faces:
        if f.Surface.TypeId != "Part::GeomCylinder":
            continue
        r = f.Surface.Radius
        if r < 0.3 or r > 8:
            continue
        c_local = f.Surface.Center
        c = to_world(c_local)
        # 只关心前脸附近（世界 y < -124）的特征
        if c.y > -124:
            continue
        ax = ROT.multVec(f.Surface.Axis)
        key = (round(r, 2), round(c.x, 1), round(c.z, 1))
        if key in seen:
            continue
        seen.add(key)
        w("  r=%.2f (D=%.2f) 中心世界 (x=%.2f, y=%.2f, z=%.2f) 轴(%.2f,%.2f,%.2f) 面积 %.1f" % (
            r, 2*r, c.x, c.y, c.z, ax.x, ax.y, ax.z, f.Area))
App.closeDocument("m")

w("")
w("===== TOF后支架.FCStd 现有圆柱孔（世界坐标 z+1.5）=====")
doc2 = App.openDocument(r"E:/car_projects/freecad/parts/TOF后支架.FCStd")
seen2 = set()
for o in doc2.Objects:
    if not hasattr(o, "Shape") or not o.Shape.Solids:
        continue
    for f in o.Shape.Faces:
        if f.Surface.TypeId != "Part::GeomCylinder":
            continue
        r = f.Surface.Radius
        if r < 0.3 or r > 8:
            continue
        c = f.Surface.Center
        key = (round(r, 2), round(c.x, 1), round(c.z + 1.5, 1))
        if key in seen2:
            continue
        seen2.add(key)
        w("  r=%.2f (D=%.2f) 中心 (x=%.2f, y=%.2f, z=%.2f) 轴(%.2f,%.2f,%.2f)" % (
            r, 2*r, c.x, c.y, c.z + 1.5,
            f.Surface.Axis.x, f.Surface.Axis.y, f.Surface.Axis.z))
w("DONE")
