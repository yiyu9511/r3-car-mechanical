# -*- coding: utf-8 -*-
import sys
import Part
import FreeCAD as App

def holes_in_file(path, label, rmin=0.9, rmax=2.6, min_z_span=0.0):
    print("\n===== %s =====" % label)
    print("file:", path)
    try:
        shape = Part.read(path)
    except Exception as e:
        print("READ FAIL:", e)
        return None
    bb = shape.BoundBox
    print("TOTAL bbox X[%.1f,%.1f] Y[%.1f,%.1f] Z[%.1f,%.1f]" % (bb.XMin,bb.XMax,bb.YMin,bb.YMax,bb.ZMin,bb.ZMax))
    holes = []
    for f in shape.Faces:
        s = f.Surface
        if s.TypeId == 'Part::GeomCylinder':
            r = s.Radius
            if rmin <= r <= rmax:
                c = s.Center
                ax = s.Axis
                # only near-vertical holes
                if abs(ax.z) > 0.9:
                    holes.append((c.x, c.y, c.z, r))
    # cluster by radius
    from collections import defaultdict
    byr = defaultdict(list)
    for h in holes:
        byr[round(h[3],2)].append(h)
    for r in sorted(byr):
        hs = byr[r]
        print("  r=%.2f (D=%.1f) x%d:" % (r, 2*r, len(hs)))
        seen = set()
        for x,y,z,r2 in hs:
            key = (round(x,1), round(y,1))
            if key in seen: continue
            seen.add(key)
            print("    (%.2f, %.2f) z=%.2f" % (x, y, z))
    return shape

jobs = [
    (r"E:/car_projects/lubancat/LubanCat 5-PCB 3D文件.STEP", "LubanCat5 PCB"),
    (r"E:/car_projects/freecad/models/E351S电池(客户图）.stp", "E351S battery"),
    (r"E:/car_projects/freecad/models/单线雷达总装.STEP", "Radar"),
    (r"E:/car_projects/freecad/models/TOFSense_F2_Mini_Appearance_V1.0.step", "TOFSense F2"),
    (r"E:/car_projects/freecad/models/TOFSense_M_S_Appearance_V1.0.step", "TOFSense M"),
    (r"E:/car_projects/freecad/models/RT8279稳压模块PCB模型文件.step", "RT8279"),
]
with open(r"E:/car_projects/freecad/output/holes_report.txt", "w", encoding="utf-8") as fout:
    import io
    real = sys.stdout
    class Tee(io.TextIOBase):
        def write(self, s):
            real.write(s); fout.write(s)
        def flush(self):
            real.flush(); fout.flush()
    sys.stdout = Tee()
    for p, lab in jobs:
        holes_in_file(p, lab)
