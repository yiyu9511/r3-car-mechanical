# -*- coding: utf-8 -*-
# 对比实验：STEP(B-rep) 布尔 vs STL网格转实体 布尔 —— 同一对 TOF后支架 × TOF-F2
# 用法: freecadcmd.exe check_step_speed.py
import sys, time

LOG = r"E:/car_projects/freecad/output/step_vs_stl_speed.txt"
def w(s):
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(s + "\n")
    sys.stdout.write(s + "\n"); sys.stdout.flush()
open(LOG, "w").close()

import FreeCAD as App
from FreeCAD import Base
import Part, Import, Mesh

def bracket_solid():
    """从 FCStd 取支架实体，平移到世界系（z+1.5）"""
    doc = App.openDocument(r"E:/car_projects/freecad/parts/TOF后支架.FCStd")
    shapes = [o.Shape for o in doc.Objects if hasattr(o, "Shape") and o.Shape.Solids]
    comp = Part.makeCompound([s for o_shape in shapes for s in o_shape.Solids])
    comp.translate(Base.Vector(0, 0, 1.5))
    return comp

# ---------- 路线 A：STEP 原生 B-rep ----------
t0 = time.time()
doc = App.newDocument("f2step")
Import.insert(r"E:/car_projects/freecad/models/TOFSense_F2_Mini_Appearance_V1.0.step", "f2step")
shapes = [o.Shape for o in doc.Objects if hasattr(o, "Shape") and o.Shape.Solids]
w("A: F2 STEP solids=%d" % sum(len(s.Solids) for s in shapes))
f2 = Part.makeCompound([s for shape in shapes for s in shape.Solids])
# 世界变换: Rx(+90) (x,y,z)->(x,-z,y)，再 t=(0,-125.5,7.5)
f2 = f2.transformGeometry(Base.Matrix(  # 旋转
    1, 0, 0, 0,
    0, 0, -1, 0,
    0, 1, 0, 0,
    0, 0, 0, 1))
f2.translate(Base.Vector(0, -125.5, 7.5))
t1 = time.time()
brk = bracket_solid()
t2 = time.time()
common_a = brk.common(f2)
t3 = time.time()
w("A: 载入+变换 STEP  %.2fs | 载入支架FCStd %.2fs | 布尔common %.2fs" % (t1-t0, t2-t1, t3-t2))
w("A: 干涉体积 = %.4f mm^3" % common_a.Volume)
if common_a.Volume > 0.01:
    bb = common_a.BoundBox
    w("A: 区域 X[%.2f,%.2f] Y[%.2f,%.2f] Z[%.2f,%.2f]" % (bb.XMin, bb.XMax, bb.YMin, bb.YMax, bb.ZMin, bb.ZMax))
App.closeDocument("f2step")

# ---------- 路线 B：STL 网格转实体 ----------
t0 = time.time()
m = Mesh.Mesh(r"E:/car_projects/freecad/output/stl/器件_TOF-F2.stl")
sh = Part.Shape()
sh.makeShapeFromMesh(m.Topology, 0.05, True)
t1 = time.time()
w("B: 器件 STL(%d 面) 缝合 %.2fs" % (m.CountFacets, t1-t0))
try:
    f2m = Part.makeSolid(sh)
except Exception as e:
    f2m = sh  # 可能是壳体
    w("B: makeSolid 失败(%s)，用 shell" % e)
t2 = time.time()
m2 = Mesh.Mesh(r"E:/car_projects/freecad/output/stl/TOF后支架.stl")
sh2 = Part.Shape()
sh2.makeShapeFromMesh(m2.Topology, 0.05, True)
brk2 = Part.makeSolid(sh2)
brk2.translate(Base.Vector(0, 0, 1.5))
t3 = time.time()
w("B: 支架 STL(%d 面) 缝合+实体 %.2fs" % (m2.CountFacets, t3-t2))
common_b = brk2.common(f2m)
t4 = time.time()
w("B: 布尔common %.2fs | 总计 %.2fs" % (t4-t3, t4-t0))
w("B: 干涉体积 = %.4f mm^3" % common_b.Volume)
w("DONE")
