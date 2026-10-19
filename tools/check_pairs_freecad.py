# -*- coding: utf-8 -*-
# 用 FreeCAD 实体布尔 common 做真·碰撞检测（无头）
# 用法: freecadcmd.exe check_pairs_freecad.py
import sys

LOG = r"E:/car_projects/freecad/output/interference_report.txt"
def w(s):
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(s + "\n")
    sys.stdout.write(s + "\n"); sys.stdout.flush()
open(LOG, "w").close()

import Mesh, Part
from FreeCAD import Base

STL = r"E:/car_projects/freecad/output/stl/%s.stl"
Z = {"设备塔": 1.5, "TOF后支架": 1.5, "前传感器支架B": 1.5,
     "LubanCat转接板": 53.5, "雷达转接板": 53.5}

PAIRS = [
    ("TOF后支架", "器件_TOF-F2"),
    ("前传感器支架B", "器件_TOF-M"),
    ("设备塔", "器件_F407"),
    ("设备塔", "器件_TB6612"),
    ("设备塔", "器件_RT8279"),
    ("LubanCat转接板", "器件_LubanCat"),
    ("雷达转接板", "器件_雷达"),
    ("雷达转接板", "器件_相机B"),
    ("雷达转接板", "器件_LubanCat"),
    ("雷达转接板", "LubanCat转接板"),
]

def solid_of(tag):
    m = Mesh.Mesh(STL % tag)
    sh = Part.Shape()
    sh.makeShapeFromMesh(m.Topology, 0.05, True)  # sew
    sol = Part.makeSolid(sh)
    z = Z.get(tag, 0)
    if z:
        sol.translate(Base.Vector(0, 0, z))
    return sol

w("===== FreeCAD 实体布尔干涉检测（方案B装配）=====")
for t1, t2 in PAIRS:
    try:
        s1, s2 = solid_of(t1), solid_of(t2)
    except Exception as e:
        w("SKIP %s vs %s: 网格转实体失败 %s" % (t1, t2, e)); continue
    try:
        common = s1.common(s2)
        vol = common.Volume
    except Exception as e:
        w("FAIL %s vs %s: 布尔失败 %s" % (t1, t2, e)); continue
    if vol > 0.01:  # mm^3
        bb = common.BoundBox
        w("[干涉] %s vs %s  体积=%.2f mm^3" % (t1, t2, vol))
        w("       区域 X[%.2f,%.2f] Y[%.2f,%.2f] Z[%.2f,%.2f]" % (
            bb.XMin, bb.XMax, bb.YMin, bb.YMax, bb.ZMin, bb.ZMax))
    else:
        w("[OK]   %s vs %s  (%.4f mm^3)" % (t1, t2, vol))
w("DONE")
