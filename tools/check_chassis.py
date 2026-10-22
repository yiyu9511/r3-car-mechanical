# -*- coding: utf-8 -*-
# 检查底板_4 是否有圆柱面孔特征（判断是 STEP 实体还是网格）
import sys
LOG = r"E:/car_projects/freecad/output/chassis_check.txt"
def w(s):
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(s + "\n")
    sys.stdout.write(s + "\n"); sys.stdout.flush()
open(LOG, "w").close()
import FreeCAD as App
doc = App.openDocument(r"E:/car_projects/freecad/self_test.FCStd")
for o in doc.Objects:
    if "底板" in o.Label and hasattr(o, "Shape"):
        sh = o.Shape
        w("底板_4: Faces=%d Edges=%d TypeId=%s" % (len(sh.Faces), len(sh.Edges), o.TypeId))
        # 统计圆柱面
        from collections import Counter
        cy = Counter()
        for f in sh.Faces:
            if f.Surface.TypeId == "Part::GeomCylinder":
                cy[round(f.Surface.Radius, 1)] += 1
        w("圆柱面半径分布(半径:数量): %s" % dict(cy))
        # 打印所有 r 在 1.0~2.0 的圆柱中心（孔）
        seen = set()
        for f in sh.Faces:
            if f.Surface.TypeId == "Part::GeomCylinder" and 1.0 <= f.Surface.Radius <= 2.0:
                c = f.Surface.Center
                key = (round(f.Surface.Radius, 2), round(c.x, 1), round(c.y, 1))
                if key in seen:
                    continue
                seen.add(key)
                w("  Ø%.2f @ (%.1f, %.1f) 轴z=%.2f" % (2*f.Surface.Radius, c.x, c.y, f.Surface.Axis.z))
w("DONE")
