# -*- coding: utf-8 -*-
import math, json, sys, traceback
import FreeCAD as App
import Part

LOG = open(r"E:/car_projects/freecad/output/build_report.txt", "w", encoding="utf-8")
def log(*a):
    s = " ".join(str(x) for x in a)
    LOG.write(s + "\n"); LOG.flush()
    sys.stdout.write(s + "\n"); sys.stdout.flush()

try:
    OUT_PLATE = r"E:/car_projects/freecad/parts/上层板.FCStd"
    OUT_PLATFORM = r"E:/car_projects/freecad/parts/雷达平台.FCStd"
    outline = json.load(open(r"E:/car_projects/freecad/output/upper_plate_outline.json"))
    log("outline pts:", len(outline))

    R_M3, R_M25 = 1.6, 1.4
    holes_plate = []
    def add(cx, cy, w, h, r, tag):
        for sx in (-1,1):
            for sy in (-1,1):
                holes_plate.append((cx+sx*w/2, cy+sy*h/2, r, tag))

    for x,y in [(50,80),(-50,80),(50,-10),(-50,-10),(50,-90),(-50,-90)]:
        holes_plate.append((x,y,R_M3,"standoff"))
    add(0,0,117.98,72.98,R_M3,"lubancat")
    add(8,-15,44,44,R_M3,"tb6612")
    add(-40,40,34.788,62.484,R_M3,"f407")
    add(35,60,41.27,18.68,R_M3,"rt8279")
    for x,y in [(30,-52),(-30,-52),(30,52),(-30,52)]:
        holes_plate.append((x,y,R_M3,"platform_leg"))
    for x,y in [(12,92),(-12,92),(24,95),(-24,95)]:
        holes_plate.append((x,y,R_M3,"front_bracket"))
    log("holes:", len(holes_plate))

    def min_dist_to_edge(x,y):
        best = 1e9
        n = len(outline)
        for i in range(n):
            x1,y1 = outline[i]; x2,y2 = outline[(i+1)%n]
            dx,dy = x2-x1, y2-y1
            L2 = dx*dx+dy*dy
            if L2 == 0: continue
            t = max(0,min(1,((x-x1)*dx+(y-y1)*dy)/L2))
            px,py = x1+t*dx, y1+t*dy
            best = min(best, math.hypot(x-px,y-py))
        return best

    warn = []
    hs = [(x,y,r) for x,y,r,_ in holes_plate]
    for i,(x,y,r,t) in enumerate(holes_plate):
        e = min_dist_to_edge(x,y) - r
        if e < 2.5:
            warn.append("EDGE %-14s (%.1f,%.1f) lig=%.2f" % (t,x,y,e))
        for j in range(i+1,len(hs)):
            x2,y2,r2 = hs[j]
            d = math.hypot(x-x2,y-y2) - r - r2
            if d < 2.0:
                warn.append("CLASH %-14s(%.1f,%.1f) vs %-14s(%.1f,%.1f) gap=%.2f" % (t,x,y,holes_plate[j][3],x2,y2,d))
    log("CHECK warnings:", len(warn))
    for w in warn: log("  !!", w)

    def build_plate(name, outline_pts, holes, thick, outfile):
        doc = App.newDocument(name)
        vecs = [App.Vector(x,y,0) for x,y in outline_pts] + [App.Vector(outline_pts[0][0], outline_pts[0][1], 0)]
        face = Part.Face(Part.makePolygon(vecs))
        solid = face.extrude(App.Vector(0,0,thick))
        for x,y,r,tag in holes:
            solid = solid.cut(Part.makeCylinder(r, thick+2, App.Vector(x,y,-1)))
        obj = doc.addObject("Part::Feature", name)
        obj.Shape = solid
        doc.recompute()
        doc.saveAs(outfile)
        App.closeDocument(doc.Name)
        log("SAVED", outfile, "valid:", solid.isValid(), "faces:", len(solid.Faces))
        return solid

    if not warn:
        build_plate("上层板", outline, holes_plate, 2.0, OUT_PLATE)
        plat_outline = [(-42,-62),(42,-62),(42,62),(-42,62)]
        holes_plat = [(30,-52,R_M3,"leg"),(-30,-52,R_M3,"leg"),(30,52,R_M3,"leg"),(-30,52,R_M3,"leg")]
        for sx in (-1,1):
            for sy in (-1,1):
                holes_plat.append((sx*26.61, sy*26.61, R_M25, "radar"))
        build_plate("雷达平台", plat_outline, holes_plat, 2.0, OUT_PLATFORM)
    else:
        log("ABORT: warnings exist, parts NOT rebuilt")
    log("DONE")
except Exception:
    log("EXCEPTION:")
    log(traceback.format_exc())
finally:
    LOG.close()
