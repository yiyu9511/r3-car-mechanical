# -*- coding: utf-8 -*-
# 穷举 TOFSense F2 STEP 前脸平面上的所有圆形边界（= 真实开孔），不做任何半径过滤
# 用法: freecadcmd.exe dump_f2_face_holes.py
import sys

LOG = r"E:/car_projects/freecad/output/f2_face_holes.txt"
def w(s):
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(s + "\n")
    sys.stdout.write(s + "\n"); sys.stdout.flush()
open(LOG, "w").close()

import FreeCAD as App
from FreeCAD import Base
import Import

ROT = Base.Matrix(1,0,0,0, 0,0,-1,0, 0,1,0,0, 0,0,0,1)
T = Base.Vector(0, -125.5, 7.5)
def wd(p):
    q = ROT.multVec(p)
    return Base.Vector(q.x+T.x, q.y+T.y, q.z+T.z)

doc = App.newDocument("f2")
Import.insert(r"E:/car_projects/freecad/models/TOFSense_F2_Mini_Appearance_V1.0.step", "f2")

w("== 全局圆形边（不按面筛），世界坐标 ==")
w("%-8s %-9s %-26s %s" % ("D", "y世界", "圆心(x,z)世界", "来源"))
allcircles = {}
for o in doc.Objects:
    if not hasattr(o, "Shape") or not o.Shape.Faces:
        continue
    for e in o.Shape.Edges:
        try:
            c = e.Curve
        except Exception:
            continue
        if c.TypeId != "Part::GeomCircle":
            continue
        r = c.Radius
        ctr = wd(c.Center)
        key = (round(2*r, 2), round(ctr.x, 2), round(ctr.y, 2), round(ctr.z, 2))
        if key in allcircles:
            allcircles[key] += 1
        else:
            allcircles[key] = 1

rows = sorted(allcircles.items(), key=lambda kv: (kv[0][2], kv[0][3], kv[0][1]))
last_y = None
for (d, x, y, z), n in rows:
    if last_y is None or abs(y - last_y) > 0.05:
        w("--- 平面 y = %.2f ---" % y)
        last_y = y
    w("D=%-6.2f  x=%-7.2f z=%-7.2f  边数=%d" % (d, x, z, n))
w("DONE")
