# 鲁班猫 5 PCB 简化: 只保留 PCB 板体(含全部孔), 元器件全部移除。
# 运行: cadgen run scripts/simplify_lubancat.py
import os

import build123d as bd
from build123d import import_step
from OCP.BRepAdaptor import BRepAdaptor_Surface
from OCP.GeomAbs import GeomAbs_Cylinder

BASE = os.path.dirname(__file__)
SRC = os.path.join(BASE, "..", "..", "freecad", "models", "LubanCat 5-PCB 3D文件.STEP")
OUT_STEP = os.path.join(BASE, "..", "exports", "LubanCat5_PCB_simplified.step")
OUT_HOLES = os.path.join(BASE, "..", "exports", "LubanCat5_PCB_holes.txt")

sh = import_step(SRC)
solids = sh.solids()
print(f"source solids: {len(solids)}")

# 板 = 厚度 < 5mm 且 XY 面积最大的闭合实体
def probe(s):
    b = s.bounding_box()
    return b.size.X * b.size.Y * (1 if b.size.Z < 5 else 0)

board = max(solids, key=probe)
b = board.bounding_box()
print(f"board: {b.size.X:.1f} x {b.size.Y:.1f} x {b.size.Z:.2f} mm, vol={board.volume:.0f}")

board.label = "LubanCat5_PCB"
board.color = "#1a6b3c"
bd.export_step(board, OUT_STEP)
print(f"exported: {OUT_STEP}")

# 孔位清单 (轴向 Z 的圆柱面)
holes = set()
for f in board.faces():
    ad = BRepAdaptor_Surface(f.wrapped)
    if ad.GetType() != GeomAbs_Cylinder:
        continue
    cyl = ad.Cylinder()
    if abs(abs(cyl.Axis().Direction().Z()) - 1) > 1e-3:
        continue
    loc = cyl.Location()
    holes.add((round(loc.X(), 2), round(loc.Y(), 2), round(cyl.Radius() * 2, 2)))
holes = sorted(holes)
with open(OUT_HOLES, "w", encoding="utf-8") as fh:
    fh.write("x_mm\ty_mm\tdia_mm\n")
    for x, y, d in holes:
        fh.write(f"{x}\t{y}\t{d}\n")
print(f"Z-axis holes: {len(holes)} -> {OUT_HOLES}")
