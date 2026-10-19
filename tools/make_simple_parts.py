# -*- coding: utf-8 -*-
# make_simple_parts.py — 生成装配验证用的简化零件模型
#
# 用法（FreeCAD 内）：
#   宏 → 宏… → 创建 → 打开本文件 → 运行（或复制到宏目录后运行）
# 产物：
#   E:\car_projects\freecad\parts\IMX415摄像头模组_简化.FCStd
#   E:\car_projects\freecad\parts\F407VE开发板_简化.FCStd   ⚠️尺寸为占位值
#
# 简化模型的目标：外形尺寸、安装孔位、高度占空间正确即可，不追求外观。
# 所有尺寸集中在下面两个参数区，实测后直接改数重跑。

import os
import FreeCAD as App
import Part
from FreeCAD import Vector

OUT_DIR = r"E:\car_projects\freecad\parts"

# ================= 摄像头模组 IMX415（EBF410358V1R1） =================
# 来源：EBF410358V1R1_PCB_尺寸图_20260402.pdf（ART FILM - TOP）
#   外形 29 × 31.25；孔 M2.5×4；角 R3×4（V1R0 背面图标注）
# ⚠️ 孔距 23×24 是从图纸判读的，装机前用卡尺复核实物
CAM_L   = 29.0     # 板宽 X
CAM_W   = 31.25    # 板长 Y
CAM_T   = 1.2      # 板厚（常规 1.2，实测改）
CAM_R   = 3.0      # 圆角
CAM_HD  = 2.5      # 安装孔径（M2.5）
CAM_HX  = 23.0     # 横向孔距
CAM_HY  = 24.0     # 纵向孔距
# 顶部占位件（传感器+镜头座、FPC 连接器）：只保证高度方向不撞
CAM_SENSOR_LWH = (10.0, 10.0, 4.5)   # ⚠️镜头座实际更高，装镜头后按实测改
CAM_FPC_LWH    = (13.0, 4.0, 2.0)    # 24P FPC 座

# ================= F407VET6 Mini（芯路城 Micro USB 款）=================
# ✅ 尺寸实锤，来源与解析见 docs/ref/F407板尺寸来源.md
# （芯路城官网 pcbdoc ASCII 解析 + 官网尺寸图 size.png，两源互证）
F407_L   = 40.894  # 板宽 X（板框 Track 实测值）
F407_W   = 68.591  # 板高 Y
F407_T   = 1.6     # 板厚 ⚠️待实测
F407_HAS_HOLES = True
F407_HD  = 3.2     # 固定孔径（规格 3mm，孔含镀铜 3.2）
F407_HX  = 34.788  # 横向孔距（pcbdoc 79.253↔114.041）
F407_HY  = 62.484  # 纵向孔距（pcbdoc 79.253↔141.737）
F407_USB_LWH = (7.5, 10.0, 5.5)      # Micro USB 座 ⚠️位置/凸出待实测
F407_HDR_LWH = (5.1, 55.9, 8.5)      # 左右各一双排 2×22（排距2.54+针长）
F407_HDR_ROW_X = 17.78               # 排针组中心到板中心（77.6+80.14)/2-96.65≈±17.78
F407_HAS_HDR = True                  # 手工建模可省略排针占位


def filleted_plate(l, w, t, r):
    """圆角矩形板，中心在原点，顶面朝 +Z。"""
    plate = Part.makeBox(l, w, t, Vector(-l/2, -w/2, 0))
    edges = [e for e in plate.Edges
             if abs(e.Vertexes[0].Point.z - e.Vertexes[-1].Point.z) > t/2]
    return plate.makeFillet(r, edges)


def add_holes(solid, dia, hx, hy, depth):
    """四角对称打孔（中心对称 4 孔）。"""
    for sx in (-1, 1):
        for sy in (-1, 1):
            c = Part.makeCylinder(dia/2, depth + 2,
                                  Vector(sx*hx/2, sy*hy/2, -1))
            solid = solid.cut(c)
    return solid


def make_doc(name):
    old = App.ActiveDocument
    doc = App.newDocument(name)
    return doc


def build_camera():
    doc = make_doc("IMX415摄像头模组_简化")
    pcb = filleted_plate(CAM_L, CAM_W, CAM_T, CAM_R)
    pcb = add_holes(pcb, CAM_HD, CAM_HX, CAM_HY, CAM_T)
    obj = doc.addObject("Part::Feature", "PCB")
    obj.Shape = pcb

    sl, sw, sh = CAM_SENSOR_LWH
    sensor = Part.makeBox(sl, sw, sh, Vector(-sl/2, -sw/2 + 3, CAM_T))
    o2 = doc.addObject("Part::Feature", "传感器镜头座占位")
    o2.Shape = sensor

    fl, fw, fh = CAM_FPC_LWH
    fpc = Part.makeBox(fl, fw, fh, Vector(-fl/2, -CAM_W/2 + 2, CAM_T))
    o3 = doc.addObject("Part::Feature", "FPC座占位")
    o3.Shape = fpc

    path = os.path.join(OUT_DIR, "IMX415摄像头模组_简化.FCStd")
    doc.saveAs(path)
    App.Console.PrintMessage("已保存: %s\n" % path)
    return doc


def build_f407():
    doc = make_doc("F407VE开发板_简化")
    pcb = Part.makeBox(F407_L, F407_W, F407_T,
                       Vector(-F407_L/2, -F407_W/2, 0))
    if F407_HAS_HOLES:
        pcb = add_holes(pcb, F407_HD, F407_HX, F407_HY, F407_T)
    obj = doc.addObject("Part::Feature", "PCB")
    obj.Shape = pcb

    ul, uw, uh = F407_USB_LWH
    usb = Part.makeBox(ul, uw, uh, Vector(-ul/2, -F407_W/2 - 1, F407_T))
    o2 = doc.addObject("Part::Feature", "USB座占位")
    o2.Shape = usb

    hl, hw, hh = F407_HDR_LWH
    for side in (-1, 1):
        hdr = Part.makeBox(hw, hl, hh,
                           Vector(side*F407_HDR_ROW_X - hw/2, -hl/2, F407_T))
        o3 = doc.addObject("Part::Feature", "排针占位_%s" % ("L" if side < 0 else "R"))
        o3.Shape = hdr

    path = os.path.join(OUT_DIR, "F407VE开发板_简化.FCStd")
    doc.saveAs(path)
    App.Console.PrintMessage("已保存: %s\n" % path)
    return doc


build_camera()
build_f407()
App.Console.PrintMessage("完成。装配时从 assemblies 文档插入这两个 FCStd 即可。\n")
