from build123d import import_step
from OCP.StlAPI import StlAPI_Writer
from OCP.gp import gp_Trsf
from OCP.BRepBuilderAPI import BRepBuilderAPI_Transform
from OCP.BRepMesh import BRepMesh_IncrementalMesh
BASE = r"E:\car_projects\cad_solidcraft\exports"

def bake(src, out, tvec):
    sh = import_step(src)
    t = gp_Trsf()
    t.SetValues(1,0,0,tvec[0], 0,1,0,tvec[1], 0,0,1,tvec[2])
    wshape = BRepBuilderAPI_Transform(sh.wrapped, t, True).Shape()
    BRepMesh_IncrementalMesh(wshape, 0.15, False, 0.5, True)
    w = StlAPI_Writer()
    w.ASCIIMode = False
    print(out.split("\\")[-1], "write:", w.Write(wshape, out))

bake(r"E:\car_projects\freecad\models\C30D-V2.2_2026.04.20.stp",
     BASE + r"\C30D_stl.stl", (29.1817, -11.5204, 7.5))
bake(BASE + r"\lidar_z0.step",
     BASE + r"\lidar_stl.stl", (0, 55, 86))
