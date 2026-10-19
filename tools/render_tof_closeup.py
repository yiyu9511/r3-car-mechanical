# -*- coding: utf-8 -*-
# 后 TOF 局部特写：器件 + 支架半透明，三个视角
import pyvista as pv

dev = pv.read(r"E:/car_projects/freecad/output/stl/器件_TOF-F2.stl")
brk = pv.read(r"E:/car_projects/freecad/output/stl/TOF后支架.stl")
brk.translate((0, 0, 1.5), inplace=True)

VIEWS = {
    "rear":   [(0, -190, 12), (0, -120, 11), (0, 0, 1)],   # 车尾看前脸
    "side":   [(60, -122, 12), (0, -122, 11), (0, 0, 1)],  # 侧面看墙/镜头
    "top":    [(0, -122, 90), (0, -122, 11), (0, 1, 0)],   # 俯视看插接方向
}
for name, cam in VIEWS.items():
    pl = pv.Plotter(off_screen=True, window_size=(1200, 900))
    pl.set_background("white")
    pl.add_mesh(dev, color="#e8a050", smooth_shading=False)
    pl.add_mesh(brk, color="#4080c0", opacity=0.45, smooth_shading=False)
    pl.render()
    pl.camera_position = cam
    pl.render()
    out = r"E:/car_projects/freecad/output/renders/tof_f2_%s.png" % name
    pl.screenshot(out)
    pl.close()
    print("saved", out)
print("DONE")
