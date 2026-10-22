# -*- coding: utf-8 -*-
# 实测 self_test.FCStd 里 LubanCat 外壳底部的固定孔位置 + 底板可用锚点
import sys
LOG = r"E:/car_projects/freecad/output/cat_hole_measure.txt"
def w(s):
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(s + "\n")
    sys.stdout.write(s + "\n"); sys.stdout.flush()
open(LOG, "w").close()

import FreeCAD as App
from FreeCAD import Base

doc = App.openDocument(r"E:/car_projects/freecad/self_test.FCStd")

# 外壳底部的 M3x9 螺丝对象 → 它们的 Placement 就是孔位
w("=== 外壳底部固定螺丝（M3x9）位置 ===")
for o in doc.Objects:
    if "M3x9" in o.Label:
        p = o.Placement.Base
        # 螺丝自身 bbox 也有用
        bb = o.Shape.BoundBox if hasattr(o, "Shape") else None
        w("%s  pos=(%.2f, %.2f, %.2f)  bbox Z[%.2f, %.2f]" % (
            o.Label, p.x, p.y, p.z,
            bb.ZMin, bb.ZMax) if bb else w("%s pos=(%.2f,%.2f,%.2f)" % (o.Label, p.x, p.y, p.z)))

# 外壳下主体（底部板）上所有圆柱面 → 找 M2.5/M3 螺纹孔的圆柱
w("")
w("=== 外壳下主体 圆柱面（可能的孔）===")
for o in doc.Objects:
    if "下主体" in o.Label and hasattr(o, "Shape"):
        seen = set()
        for f in o.Shape.Faces:
            if f.Surface.TypeId == "Part::GeomCylinder":
                r = f.Surface.Radius
                if 1.0 <= r <= 2.0:  # M2.5~M3 螺纹孔半径范围
                    c = f.Surface.Center
                    key = (round(r, 2), round(c.x, 1), round(c.y, 1), round(c.z, 1))
                    if key in seen:
                        continue
                    seen.add(key)
                    w("  r=%.2f 中心(%.2f, %.2f, %.2f) 轴(%.1f,%.1f,%.1f)" % (
                        r, c.x, c.y, c.z,
                        f.Surface.Axis.x, f.Surface.Axis.y, f.Surface.Axis.z))

# 底板上的孔（直径 2~4mm 的圆柱，看哪些是可用锚点）
w("")
w("=== 底板 圆柱面孔（Ø2~Ø4）===")
for o in doc.Objects:
    if "底板" in o.Label and hasattr(o, "Shape"):
        seen = set()
        for f in o.Shape.Faces:
            if f.Surface.TypeId == "Part::GeomCylinder":
                r = f.Surface.Radius
                if 1.0 <= r <= 2.0:
                    c = f.Surface.Center
                    key = (round(r, 2), round(c.x, 1), round(c.y, 1))
                    if key in seen:
                        continue
                    seen.add(key)
                    w("  Ø%.2f @ (%.1f, %.1f)" % (2*r, c.x, c.y))
w("DONE")
