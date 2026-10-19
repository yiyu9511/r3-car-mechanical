# -*- coding: utf-8 -*-
# 分析 TOFSense F2 Mini 外观模型：找凸起（连接器/元件）位置与尺寸
# 用法: freecadcmd.exe analyze_f2_bump.py
import sys, json

LOG = r"E:/car_projects/freecad/output/f2_bump_report.txt"

def w(s):
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(s + "\n")
    sys.stdout.write(s + "\n"); sys.stdout.flush()

open(LOG, "w").close()

import FreeCAD as App
import Import

path = r"E:/car_projects/freecad/models/TOFSense_F2_Mini_Appearance_V1.0.step"
doc = App.newDocument("f2")
Import.insert(path, "f2")

w("objects: %d" % len(doc.Objects))
for obj in doc.Objects:
    if not hasattr(obj, "Shape"):
        continue
    sh = obj.Shape
    try:
        bb = sh.BoundBox
    except Exception:
        continue
    w("== %s  type=%s  solids=%d" % (obj.Name, obj.TypeId, len(sh.Solids)))
    w("   bbox: X[%.2f, %.2f] Y[%.2f, %.2f] Z[%.2f, %.2f]" % (
        bb.XMin, bb.XMax, bb.YMin, bb.YMax, bb.ZMin, bb.ZMax))
    for i, sol in enumerate(sh.Solids):
        sb = sol.BoundBox
        w("   solid%d: vol=%.1f  X[%.2f,%.2f] Y[%.2f,%.2f] Z[%.2f,%.2f]" % (
            i, sol.Volume, sb.XMin, sb.XMax, sb.YMin, sb.YMax, sb.ZMin, sb.ZMax))
