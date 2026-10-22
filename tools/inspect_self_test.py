# -*- coding: utf-8 -*-
# 只读探查 self_test.FCStd 的对象树与位置，不动文件
import sys
LOG = r"E:/car_projects/freecad/output/self_test_inspect.txt"
def w(s):
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(s + "\n")
    sys.stdout.write(s + "\n"); sys.stdout.flush()
open(LOG, "w").close()

import FreeCAD as App
doc = App.openDocument(r"E:/car_projects/freecad/self_test.FCStd")
w("=== self_test.FCStd 对象 ===")
for o in doc.Objects:
    try:
        bb = o.Shape.BoundBox if hasattr(o, "Shape") else None
        bbs = "  bbox X[%.1f,%.1f] Y[%.1f,%.1f] Z[%.1f,%.1f]" % (
            bb.XMin, bb.XMax, bb.YMin, bb.YMax, bb.ZMin, bb.ZMax) if bb else ""
    except Exception:
        bbs = ""
    try:
        pl = o.Placement
        pos = pl.Base
        pstr = "  pos=(%.2f,%.2f,%.2f) rot=%s" % (pos.x, pos.y, pos.z, pl.Rotation.Axis)
    except Exception:
        pstr = ""
    w("%-4s %-30s %s%s%s" % (o.Name, o.Label, o.TypeId, pstr, bbs))
w("DONE")
