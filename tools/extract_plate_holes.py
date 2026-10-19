# -*- coding: utf-8 -*-
import json
import FreeCAD as App

doc = App.openDocument(r"E:/car_projects/freecad/test1.FCStd")
plate = doc.getObject("Part__Feature430")
sh = plate.Shape
holes = []
for f in sh.Faces:
    s = f.Surface
    if s.TypeId == 'Part::GeomCylinder':
        r = s.Radius
        ax = s.Axis
        if abs(ax.z) > 0.95 and r < 11:
            c = s.Center
            holes.append({"x": round(c.x, 3), "y": round(c.y, 3), "r": round(r, 3)})
# dedupe
seen = {}
for h in holes:
    k = (round(h["x"],1), round(h["y"],1), round(h["r"],1))
    seen[k] = h
holes = sorted(seen.values(), key=lambda h: (h["r"], h["y"], h["x"]))
out = {"plate_bbox": {"xmin": sh.BoundBox.XMin, "xmax": sh.BoundBox.XMax,
                      "ymin": sh.BoundBox.YMin, "ymax": sh.BoundBox.YMax,
                      "zmin": sh.BoundBox.ZMin, "zmax": sh.BoundBox.ZMax},
       "holes": holes}
with open(r"E:/car_projects/freecad/output/chassis_holes.json", "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=1)
print("saved %d holes" % len(holes))
from collections import Counter
print(Counter(h["r"] for h in holes))
