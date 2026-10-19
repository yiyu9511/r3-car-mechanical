# -*- coding: utf-8 -*-
# 全装配体干涉检查（方案B）：所有 STL 两两顶点 containment + 侵入深度
# 用法: venv python check_all_interference.py
import os, itertools, warnings
warnings.filterwarnings("ignore")
import numpy as np
import pyvista as pv
from pyvista.core.utilities.points import vtk_points  # noqa

class cKDTree:  # 无 scipy 时用暴力分块替代（目标点抽稀到 3 万防爆内存）
    def __init__(self, pts):
        if len(pts) > 30000:
            idx = np.random.default_rng(0).choice(len(pts), 30000, replace=False)
            pts = pts[idx]
        self.pts = pts
    def query(self, q):
        # 分块暴力最近距离（点数不多够用）
        out = []
        for i in range(0, len(q), 20000):
            chunk = q[i:i+20000]
            d = np.sqrt(((chunk[:, None, :] - self.pts[None, :, :]) ** 2).sum(-1))
            out.append(d.min(1))
        return np.concatenate(out), None

STL = r"E:\car_projects\freecad\output\stl\%s.stl"
PARTS = [  # (tag, z_offset) —— 与 render_asm.py 方案B 同步
    ("底盘", 0), ("上层板", 0), ("电池", 0),
    ("器件_LubanCat", 0), ("器件_TB6612", 0), ("器件_雷达", 0),
    ("器件_TOF-M", 0), ("器件_TOF-F2", 0), ("器件_RT8279", 0),
    ("器件_F407", 0), ("器件_相机B", 0),
    ("设备塔", 1.5), ("TOF后支架", 1.5),
    ("LubanCat转接板", 53.5), ("雷达转接板", 53.5), ("前传感器支架B", 1.5),
]

meshes = {}
for tag, z in PARTS:
    p = STL % tag
    if not os.path.exists(p):
        print("MISSING", p); continue
    m = pv.read(p)
    if z: m.translate((0, 0, z), inplace=True)
    meshes[tag] = m

tags = list(meshes)
print("loaded %d parts" % len(tags))

def inside_info(a, b):
    """返回 a 的顶点侵入 b 的 (数量, 最大深度估计, bbox)；深度=到 b 顶点最近距离(低估)"""
    sel = a.select_enclosed_points(b, check_surface=False, tolerance=1e-6)
    mask = sel["SelectedPoints"].astype(bool)
    pts = a.points[mask]
    if len(pts) == 0:
        return 0, 0.0, None
    d, _ = cKDTree(b.points).query(pts.astype(np.float64))
    return len(pts), float(d.max()), pts

print("\n===== 干涉报告（深度>0.2mm 才算实锤，<=0.2 视为贴合）=====")
hits = []
for t1, t2 in itertools.combinations(tags, 2):
    a, b = meshes[t1], meshes[t2]
    # 粗筛：bbox 不相交直接跳过
    bb1, bb2 = a.bounds, b.bounds
    if any(bb1[i] > bb2[i+1] + 0.01 or bb2[i] > bb1[i+1] + 0.01 for i in (0, 2, 4)):
        continue
    n1, d1, p1 = inside_info(a, b)
    n2, d2, p2 = inside_info(b, a)
    depth = max(d1, d2)
    if depth <= 0.2:
        continue
    pts = p1 if d1 >= d2 else p2
    who = "%s陷入%s" % (t1, t2) if d1 >= d2 else "%s陷入%s" % (t2, t1)
    hits.append((depth, t1, t2, who, pts))

hits.sort(reverse=True)
for depth, t1, t2, who, pts in hits:
    print("\n[!] %s  <->  %s   侵入深度≈%.2fmm  (%s)" % (t1, t2, depth, who))
    print("    区域 X[%.1f, %.1f] Y[%.1f, %.1f] Z[%.1f, %.1f]" % (
        pts[:,0].min(), pts[:,0].max(), pts[:,1].min(), pts[:,1].max(),
        pts[:,2].min(), pts[:,2].max()))
if not hits:
    print("无 >0.2mm 的干涉")
print("\nDONE, %d hits" % len(hits))
