# -*- coding: utf-8 -*-
# 检查 器件_TOF-F2 与 TOF后支架 的干涉区域
import pyvista as pv
import numpy as np

dev = pv.read(r"E:/car_projects/freecad/output/stl/器件_TOF-F2.stl")
brk = pv.read(r"E:/car_projects/freecad/output/stl/TOF后支架.stl")
brk.translate((0, 0, 1.5), inplace=True)  # render_asm.py: TOF后支架 z 偏移 1.5

print("器件 bbox:", np.round(dev.bounds, 2))
print("支架 bbox:", np.round(brk.bounds, 2))

# 器件顶点落入支架实体内的点 = 干涉
inside = dev.select_enclosed_points(brk, tolerance=1e-6)
mask = inside["SelectedPoints"].astype(bool)
pts = dev.points[mask]
print("干涉顶点数:", len(pts))
if len(pts):
    print("干涉区 X[%.2f, %.2f] Y[%.2f, %.2f] Z[%.2f, %.2f]" % (
        pts[:,0].min(), pts[:,0].max(), pts[:,1].min(), pts[:,1].max(),
        pts[:,2].min(), pts[:,2].max()))

# 反向：支架顶点落入器件
inside2 = brk.select_enclosed_points(dev, tolerance=1e-6)
mask2 = inside2["SelectedPoints"].astype(bool)
pts2 = brk.points[mask2]
print("支架顶点陷入器件数:", len(pts2))
if len(pts2):
    print("区域 X[%.2f, %.2f] Y[%.2f, %.2f] Z[%.2f, %.2f]" % (
        pts2[:,0].min(), pts2[:,0].max(), pts2[:,1].min(), pts2[:,1].max(),
        pts2[:,2].min(), pts2[:,2].max()))

# 最近距离分布（除干涉外看贴近区域）
from scipy.spatial import cKDTree
try:
    tree = cKDTree(brk.points)
    d, _ = tree.query(dev.points)
    close = dev.points[d < 1.0]
    print("间距<1mm 的器件顶点数:", len(close))
    if len(close):
        print("贴近区 X[%.2f, %.2f] Y[%.2f, %.2f] Z[%.2f, %.2f]" % (
            close[:,0].min(), close[:,0].max(), close[:,1].min(), close[:,1].max(),
            close[:,2].min(), close[:,2].max()))
except ImportError:
    print("(no scipy, skip distance)")
