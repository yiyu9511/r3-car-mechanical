# -*- coding: utf-8 -*-
# FreeCAD Macro: cat_bracket
# Description: CAT(鲁班猫5) 支架 · 全参数化建模（Spreadsheet 驱动，改表即改模）
# Author: WorkBuddy CAD
# Version: 2.0（按 freecad-scripts skill 规范重写，孔位 = 用户 self_test 原选对称化精简）
#
# 结构：3mm 底板紧贴小车底盘（10 锚孔固定）+ 2 条跑道形肋排(17mm)从板上撑起 CAT
#       肋顶 = CAT 底面 z21.5（总垫高 20mm）
# 固定：锚孔 M3×10 从下往上 + 板上圆形沉孔埋 M3 螺母；CAT = M3×10 自攻进肋顶盲孔
# 锚孔：底盘实测 M3 孔 10 点 —— (±60,27.61)(±60,11.61)(±20,29.35)(±50,-11.46)(±44,-35.97)
# CAT ：外壳下主体 6 孔 2列×3行 (-25.86/29.14)×(7.5/0/-7.5)，立柱即在这 6 点
# 中心：φ20 走线孔对位底板大孔；锚孔 φ3.4（FDM +0.4 补偿）
#
# 用法："D:/tools/FreeCAD 1.1/bin/freecadcmd.exe" tools/cat_bracket.py
# 产物：cat_bracket.FCStd + output/cat_bracket.stl + output/cat_bracket.step
# 注意：freecadcmd 的 SystemExit 会吞 stdout，报告同时写日志文件
import os
import sys
import traceback

import FreeCAD as App
import Part
import Sketcher

# ------------------------- 路径 -------------------------
ROOT   = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # freecad/
FCSTD  = os.path.join(ROOT, "cat_bracket.FCStd")
STL    = os.path.join(ROOT, "output", "cat_bracket.stl")
STEP   = os.path.join(ROOT, "output", "cat_bracket.step")
THREEMF = os.path.join(ROOT, "output", "cat_bracket.3mf")
REPORT = os.path.join(ROOT, "output", "cat_bracket_report.txt")

# ------------------------- 参数表（名称 / 公式值 / 中文注释） -------------------------
# ★FreeCAD 坑：带负号的值直接写 "-8 mm" 会被存成字符串，表达式求值静默失败。
#   所有数值单元格一律写成 "=N mm" 公式形式，强制按带单位数量解析。
PARAMS = [
    ("lift_total", "=20 mm",     "总垫高：底板上表面 -> CAT 底面"),
    ("plate_thk",  "=3 mm",      "支架顶板厚度"),
    ("z_base",     "=1.5 mm",    "底板上表面高度（底板厚 1.5）"),
    ("plate_dx",   "=135 mm",    "顶板 X 向长度"),
    ("plate_dy",   "=85 mm",     "顶板 Y 向宽度"),
    ("plate_cy",   "=-7 mm",     "顶板中心 Y（前缘让出锚孔边距）"),
    ("corner_r",   "=3 mm",      "顶板四角圆角半径"),
    ("hole_m3",    "=3.4 mm",    "M3 通孔孔径（FDM +0.4 补偿）"),
    ("post_d",     "=10 mm",     "立柱外径"),
    ("center_d",   "=20 mm",     "中心走线孔径（对位底板 φ20）"),
    ("pilot_d",    "=2.5 mm",    "肋顶 M3 自攻底孔（盲孔，不到底板）"),
    ("pilot_dep",  "=10 mm",     "自攻底孔深（肋 17 内攻 6~8mm，远离板面）"),
    ("nut_cb_d",   "=6.5 mm",    "锚孔圆形沉孔径（M3 螺母对角 6.35 + 间隙）"),
    ("nut_cb_dep", "=2.0 mm",    "锚孔沉孔深（留 1.0mm 承压 web，螺母微凸 0.3 无碍）"),
    ("catx1",      "=-25.86 mm", "CAT 立柱位 左列 X（外壳下主体实测）"),
    ("catx2",      "=29.14 mm",  "CAT 立柱位 右列 X（两列不等距，实测）"),
    ("catya",      "=7.5 mm",    "CAT 立柱位 行1 Y"),
    ("catyb",      "=0 mm",      "CAT 立柱位 行2 Y"),
    ("catyc",      "=-7.5 mm",   "CAT 立柱位 行3 Y"),
    ("ax1", "=60 mm",    "锚孔1 ±X"), ("ay1", "=27.61 mm", "锚孔1 Y 前外"),
    ("ax2", "=60 mm",    "锚孔2 ±X"), ("ay2", "=11.61 mm", "锚孔2 Y 前内"),
    ("ax3", "=20 mm",    "锚孔3 ±X"), ("ay3", "=29.35 mm", "锚孔3 Y 前中"),
    ("ax4", "=50 mm",    "锚孔4 ±X"), ("ay4", "=-11.46 mm","锚孔4 Y 后部"),
    ("ax5", "=44 mm",    "锚孔5 ±X"), ("ay5", "=-35.97 mm","锚孔5 Y 车尾（底盘实测对称对）"),
]

# 锚孔（±X 成对），全部位于底盘实测孔上
ANCHOR_PAIRS = [("ax1", "ay1"), ("ax2", "ay2"), ("ax3", "ay3"), ("ax4", "ay4"), ("ax5", "ay5")]

_lines = []
def log(msg):
    """控制台 + 报告文件双写（freecadcmd 下 stdout 不可靠）"""
    _lines.append(str(msg))
    App.Console.PrintMessage(str(msg) + "\n")


def make_params_sheet(doc):
    """建参数表：A 列名称 / B 列公式值（设别名）/ C 列注释"""
    sheet = doc.addObject("Spreadsheet::Sheet", "Params")
    sheet.set("A1", "param"); sheet.set("B1", "value"); sheet.set("C1", "note")
    row = 2
    for name, value, note in PARAMS:
        sheet.set("A%d" % row, name)
        sheet.set("B%d" % row, value)
        sheet.set("C%d" % row, note)
        sheet.setAlias("B%d" % row, name)
        row += 1
    # 派生参数：立柱高 = 总垫高 - 板厚
    sheet.set("A%d" % row, "post_h")
    sheet.set("B%d" % row, "=lift_total - plate_thk")
    sheet.set("C%d" % row, "立柱高（派生，勿手改）")
    sheet.setAlias("B%d" % row, "post_h")
    doc.recompute()
    return sheet


def new_sketch(body, name, z_expr):
    """在 body 内建草图，Z 高度绑定表达式（不附着基准面，纯 Placement 驱动）"""
    sk = body.newObject("Sketcher::SketchObject", name)
    sk.setExpression("Placement.Base.z", z_expr)
    return sk


def dim(sk, ctype, *args):
    """加驱动尺寸约束并绑定表达式。args = (geoId[, posId], 初值, 表达式)"""
    expr = args[-1]
    cidx = sk.addConstraint(Sketcher.Constraint(ctype, *args[:-1]))
    sk.setExpression("Constraints[%d]" % cidx, expr)
    return cidx


def build_plate(body):
    """底板：矩形草图（全约束+表达式）→ Pad 3mm，紧贴小车底盘 → 四角圆角"""
    sk = new_sketch(body, "Sketch_底板轮廓", "Params.z_base")
    pts = [((-1, -1), (1, -1)), ((1, -1), (1, 1)),
           ((1, 1), (-1, 1)), ((-1, 1), (-1, -1))]
    for p1, p2 in pts:
        sk.addGeometry(Part.LineSegment(App.Vector(*p1, 0), App.Vector(*p2, 0)), False)
    for i in range(4):  # 首尾闭合
        sk.addConstraint(Sketcher.Constraint("Coincident", i, 2, (i + 1) % 4, 1))
    sk.addConstraint(Sketcher.Constraint("Horizontal", 0))
    sk.addConstraint(Sketcher.Constraint("Horizontal", 2))
    sk.addConstraint(Sketcher.Constraint("Vertical", 1))
    sk.addConstraint(Sketcher.Constraint("Vertical", 3))
    dim(sk, "DistanceX", 0, 1, -67.5, "-Params.plate_dx / 2")
    dim(sk, "DistanceY", 0, 1, -49.5, "Params.plate_cy - Params.plate_dy / 2")
    dim(sk, "DistanceX", 1, 2,  67.5, "Params.plate_dx / 2")
    dim(sk, "DistanceY", 2, 1,  35.5, "Params.plate_cy + Params.plate_dy / 2")

    pad = body.newObject("PartDesign::Pad", "Pad_底板")
    pad.Profile = sk
    pad.setExpression("Length", "Params.plate_thk")
    body.Document.recompute()

    # 四角圆角：实测筛选 4 条竖直边，半径绑表达式
    fillet = body.newObject("PartDesign::Fillet", "Fillet_圆角")
    body.Document.recompute()
    vedges = ["Edge%d" % (i + 1) for i, e in enumerate(pad.Shape.Edges)
              if abs(e.Vertexes[0].Point.x - e.Vertexes[1].Point.x) < 1e-6
              and abs(e.Vertexes[0].Point.y - e.Vertexes[1].Point.y) < 1e-6]
    fillet.Base = (pad, vedges)
    fillet.setExpression("Radius", "Params.corner_r")
    body.Document.recompute()
    return sk, pad, fillet


def build_posts(body):
    """立柱：2 条跑道形肋排 = 每条 1 矩形 + 2 圆帽，共 3 草图 3 Pad 顺序融合
    ★不用圆弧草图（1.1 求解器对多约束弧不稳）；圆帽中心 = CAT 行1/行3 孔位（孔位不变）"""
    def rib_sketch(name, cx):
        sk = new_sketch(body, name, "Params.z_base + Params.plate_thk / 2")
        pts = [((-1, -1), (1, -1)), ((1, -1), (1, 1)),
               ((1, 1), (-1, 1)), ((-1, 1), (-1, -1))]
        for p1, p2 in pts:
            sk.addGeometry(Part.LineSegment(App.Vector(p1[0] * 5, p1[1] * 7.5, 0),
                                            App.Vector(p2[0] * 5, p2[1] * 7.5, 0)), False)
        for i in range(4):
            sk.addConstraint(Sketcher.Constraint("Coincident", i, 2, (i + 1) % 4, 1))
        sk.addConstraint(Sketcher.Constraint("Horizontal", 0))
        sk.addConstraint(Sketcher.Constraint("Horizontal", 2))
        sk.addConstraint(Sketcher.Constraint("Vertical", 1))
        sk.addConstraint(Sketcher.Constraint("Vertical", 3))
        dim(sk, "DistanceX", 0, 1, -5.0, "%s - Params.post_d / 2" % cx)
        dim(sk, "DistanceX", 1, 2,  5.0, "%s + Params.post_d / 2" % cx)
        dim(sk, "DistanceY", 0, 1, -7.5, "Params.catyc")
        dim(sk, "DistanceY", 2, 1,  7.5, "Params.catya")
        return sk

    def cap_sketch(name, cx, cy_expr, cy0):
        sk = new_sketch(body, name, "Params.z_base + Params.plate_thk / 2")
        c = sk.addGeometry(Part.Circle(App.Vector(0, cy0, 0),
                                       App.Vector(0, 0, 1), 5), False)
        dim(sk, "DistanceX", c, 3, 0.0, cx)
        dim(sk, "DistanceY", c, 3, cy0, cy_expr)
        dim(sk, "Diameter", c, 10.0, "Params.post_d")
        return sk

    sks = []
    pad = None
    for i, cx in enumerate(("Params.catx1", "Params.catx2")):
        for sk in (rib_sketch("Sketch_肋排%d" % (i + 1), cx),
                   cap_sketch("Sketch_帽%d_行1" % (i + 1), cx, "Params.catya", 7.5),
                   cap_sketch("Sketch_帽%d_行3" % (i + 1), cx, "Params.catyc", -7.5)):
            sks.append(sk)
            pad = body.newObject("PartDesign::Pad", "Pad_%s" % sk.Name.replace("Sketch_", ""))
            pad.Profile = sk
            pad.setExpression("Length", "Params.post_h + Params.plate_thk / 2")
            body.Document.recompute()
    return sks, pad


def build_nut_counterbores(body):
    """锚孔圆形沉孔：10 个，板上表面向下 nut_cb_dep，埋 M3 螺母（圆形即够，好打印）"""
    sk = new_sketch(body, "Sketch_锚孔沉孔", "Params.z_base + Params.plate_thk")
    for ax, ay in ANCHOR_PAIRS:
        for sgn in (1, -1):
            c = sk.addGeometry(Part.Circle(App.Vector(0, 0, 0),
                                           App.Vector(0, 0, 1), 3.25), False)
            ex = "Params.%s" % ax if sgn > 0 else "-Params.%s" % ax
            dim(sk, "DistanceX", c, 3, 0.0, ex)
            dim(sk, "DistanceY", c, 3, 0.0, "Params.%s" % ay)
            dim(sk, "Diameter", c, 6.5, "Params.nut_cb_d")
    pocket = body.newObject("PartDesign::Pocket", "Pocket_锚孔沉孔")
    pocket.Profile = sk
    pocket.setExpression("Length", "Params.nut_cb_dep")
    body.Document.recompute()
    return sk, pocket


def build_holes(body):
    """底板孔组：10 锚孔 + 中心走线孔 → Pocket 贯通（只穿 3mm 底板）"""
    sk = new_sketch(body, "Sketch_孔组", "Params.z_base + Params.plate_thk")
    defs = []
    for ax, ay in ANCHOR_PAIRS:                       # 10 锚孔（对底盘）
        for sgn in (1, -1):
            defs.append(("Params.%s" % ax if sgn > 0 else "-Params.%s" % ax,
                         "Params.%s" % ay, "Params.hole_m3"))
    defs.append(("0", "0", "Params.center_d"))        # 中心 φ20 走线孔
    for ex, ey, ed in defs:
        c = sk.addGeometry(Part.Circle(App.Vector(0, 0, 0),
                                       App.Vector(0, 0, 1), 1.7), False)
        dim(sk, "DistanceX", c, 3, 0.0, ex)
        dim(sk, "DistanceY", c, 3, 0.0, ey)
        dim(sk, "Diameter", c, 3.4, ed)
    pocket = body.newObject("PartDesign::Pocket", "Pocket_孔组")
    pocket.Profile = sk
    pocket.Type = "ThroughAll"
    body.Document.recompute()
    return sk, pocket


def build_pilots(body):
    """CAT 固定：肋顶 6 个 φ2.5 自攻盲孔（深 pilot_dep，不到 3mm 底板）
    螺丝 M3×10 从外壳内侧下拧，攻入肋排 6~8mm"""
    sk = new_sketch(body, "Sketch_CAT孔",
                    "Params.z_base + Params.plate_thk + Params.post_h")
    for cx in ("Params.catx1", "Params.catx2"):
        for cy in ("Params.catya", "Params.catyb", "Params.catyc"):
            c = sk.addGeometry(Part.Circle(App.Vector(0, 0, 0),
                                           App.Vector(0, 0, 1), 1.25), False)
            dim(sk, "DistanceX", c, 3, 0.0, cx)
            dim(sk, "DistanceY", c, 3, 0.0, cy)
            dim(sk, "Diameter", c, 2.5, "Params.pilot_d")
    pocket = body.newObject("PartDesign::Pocket", "Pocket_CAT孔")
    pocket.Profile = sk
    pocket.setExpression("Length", "Params.pilot_dep")  # 盲孔，不是 ThroughAll
    body.Document.recompute()
    return sk, pocket


def verify(body, sketches):
    """几何校验：bbox / 体积 / 圆柱面分布 / 锚孔位置 / 草图全约束"""
    shp = body.Shape
    if shp.isNull() or not shp.isValid():
        log("★ FATAL: 实体无效")
        return False
    bb = shp.BoundBox
    log("bbox  X[%.2f, %.2f] Y[%.2f, %.2f] Z[%.2f, %.2f]" %
        (bb.XMin, bb.XMax, bb.YMin, bb.YMax, bb.ZMin, bb.ZMax))
    log("期望  X[-67.50, 67.50] Y[-49.50, 35.50] Z[1.50, 21.50]")
    log("体积 %.1f mm^3  ≈ %.1f g (PLA 1.24g/cm^3)" %
        (shp.Volume, shp.Volume / 1000 * 1.24))

    cyls = {}
    hole_centers = []   # r1.7 锚孔
    pilot_centers = []  # r1.25 自攻盲孔
    cb_centers = []     # r3.25 锚孔沉孔
    for f in shp.Faces:
        if f.Surface.TypeId == "Part::GeomCylinder":
            r = round(f.Surface.Radius, 2)
            cyls[r] = cyls.get(r, 0) + 1
            c2 = (round(f.Surface.Center.x, 2), round(f.Surface.Center.y, 2))
            if abs(r - 1.7) < 0.05:
                hole_centers.append(c2)
            elif abs(r - 1.25) < 0.05:
                pilot_centers.append(c2)
            elif abs(r - 3.25) < 0.05:
                cb_centers.append(c2)
    log("圆柱面半径分布: %s" % cyls)
    log("期望: r1.7(锚孔)x10, r1.25(自攻盲孔)x6, r3.25(锚孔沉孔)x10, r5.0(跑道帽)x4, r3.0(圆角)x4, r10.0(走线孔)x1")

    expect = [(60, 27.61), (-60, 27.61), (60, 11.61), (-60, 11.61),
              (20, 29.35), (-20, 29.35), (50, -11.46), (-50, -11.46),
              (44, -35.97), (-44, -35.97)]
    expect_pilot = [(-25.86, 7.5), (29.14, 7.5), (-25.86, 0), (29.14, 0),
                    (-25.86, -7.5), (29.14, -7.5)]
    def missing(pts, cents):
        return [q for q in pts
                if not any(abs(q[0] - c[0]) < 0.05 and abs(q[1] - c[1]) < 0.05
                           for c in cents)]
    miss = missing(expect, hole_centers) + missing(expect_pilot, pilot_centers) \
           + missing(expect, cb_centers)
    log("孔位复核(10 锚孔 r1.7 + 6 盲孔 r1.25 + 10 沉孔 r3.25): %s" %
        ("全部命中 OK" if not miss else "★缺失 %s" % (miss,)))

    ok = not miss
    for sk in sketches:
        state = "全约束 OK" if sk.FullyConstrained else "★未全约束"
        log("草图 %-16s %s" % (sk.Name, state))
        ok = ok and sk.FullyConstrained
    return ok


def main():
    doc = App.newDocument("cat_bracket")
    make_params_sheet(doc)
    body = doc.addObject("PartDesign::Body", "CAT_Bracket")
    sk_plate, _, _ = build_plate(body)
    sk_posts, _ = build_posts(body)
    sk_hole, _ = build_holes(body)
    sk_cat, _ = build_pilots(body)
    sk_nut, _ = build_nut_counterbores(body)
    for o in body.Group:
        st = ""
        try:
            st = "null" if o.Shape.isNull() else ("valid" if o.Shape.isValid() else "INVALID")
        except Exception:
            st = "no-shape"
        log("[feature] %-18s %-10s %s" % (o.Name, o.TypeId.split("::")[-1], st))

    ok = verify(body, [sk_plate] + sk_posts + [sk_hole, sk_cat, sk_nut])
    if not ok:
        log("★ 校验未通过，不导出")
        return 1

    doc.saveAs(FCSTD)
    import Mesh
    Mesh.export([body], STL)
    Mesh.export([body], THREEMF)   # 打印用 3MF（含单位语义，切片软件直读）
    Part.export([body], STEP)
    log("已保存: %s" % FCSTD)
    log("已导出: %s" % STL)
    log("已导出: %s" % THREEMF)
    log("已导出: %s" % STEP)
    return 0


if __name__ == "__main__" or True:  # freecadcmd 直接执行脚本，无 __main__ 语义
    try:
        rc = main()
    except SystemExit:
        raise
    except Exception:
        log("ERROR:\n" + traceback.format_exc())
        rc = 2
    finally:
        with open(REPORT, "w", encoding="utf-8") as f:
            f.write("\n".join(_lines) + "\n")
