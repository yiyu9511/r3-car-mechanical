# -*- coding: utf-8 -*-
"""用 pyvista 离屏渲染装配体截图（无需打开 FreeCAD GUI）。
用法: python render_asm.py
输出: output/renders/{A,B}_{iso,top,side,front,catbase}.png
"""
import os
import pyvista as pv

STL = r"E:\car_projects\freecad\output\stl\%s.stl"
OUT = r"E:\car_projects\freecad\output\renders"

# (tag, z_offset, color)
COMMON = [
    ("底盘", 0, "#b8c4cc"),
    ("上层板", 0, "#7fb3e8"),
    ("电池", 0, "#e88a8a"),
    ("器件_LubanCat", 0, "#f0c060"),
    ("器件_TB6612", 0, "#60c080"),
    ("器件_雷达", 0, "#b090e0"),
    ("器件_TOF-M", 0, "#e8a050"),
    ("器件_TOF-F2", 0, "#e8a050"),
    ("器件_RT8279", 0, "#60c0c0"),
    ("器件_F407", 0, "#1a6e1a"),
    ("设备塔", 1.5, "#d0ffd0"),
    ("TOF后支架", 1.5, "#ffe0b0"),
    ("LubanCat转接板", 53.5, "#d0ffd0"),
    ("雷达转接板", 53.5, "#e0d0ff"),
]
VA = [("前传感器支架A", 1.5, "#d0ffd0"), ("器件_相机A", 0, "#404040")]
VB = [("前传感器支架B", 1.5, "#d0ffd0"), ("相机支架L2", 53.5, "#d0ffd0"), ("器件_相机B", 0, "#404040")]

# 铜柱: (x, y, z底, 高, 半径)
PILLARS = ([(x, y, 1.5, 50, 2.75) for x, y in
            [(50,80),(-50,80),(50,-10),(-50,-10),(50,-90),(-50,-90)]] +
           [(sx*58.99, yy, 56.5, 6, 2.0) for sx in (-1,1) for yy in (-50.49,22.49)])

VIEWS = {
    "iso":     [(320, 320, 300), (0, -10, 40), (0, 0, 1)],
    "top":     [(0, -10, 420), (0, -10, 0), (0, 1, 0)],
    "side":    [(420, -10, 60), (0, -10, 40), (0, 0, 1)],
    "front":   [(0, 420, 60), (0, 0, 40), (0, 0, 1)],
    "catbase": [(180, -160, 110), (0, -14, 60), (0, 0, 1)],  # LubanCat 底部特写
}

def render(tags, prefix):
    pl = pv.Plotter(off_screen=True, window_size=(1600, 1200))
    pl.set_background("white")
    for tag, z, color in tags:
        path = STL % tag
        if not os.path.exists(path):
            print("MISSING", path)
            continue
        mesh = pv.read(path)
        if z:
            mesh.translate((0, 0, z), inplace=True)
        pl.add_mesh(mesh, color=color, smooth_shading=False)
    for x, y, z0, h, r in PILLARS:
        pl.add_mesh(pv.Cylinder(center=(x, y, z0 + h/2.0), direction=(0, 0, 1),
                                radius=r, height=h), color="#c8a860")
    pl.render()  # 先建场景
    for vname, (pos, focal, up) in VIEWS.items():
        pl.camera_position = [pos, focal, up]
        pl.render()
        out = os.path.join(OUT, "%s_%s.png" % (prefix, vname))
        pl.screenshot(out)
        print("saved", out)
    pl.close()

os.makedirs(OUT, exist_ok=True)
render(COMMON + VA, "A")
render(COMMON + VB, "B")
print("DONE")
