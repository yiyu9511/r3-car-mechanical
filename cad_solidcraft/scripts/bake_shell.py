from build123d import import_step
from OCP.StlAPI import StlAPI_Writer
from OCP.gp import gp_Trsf
from OCP.BRepBuilderAPI import BRepBuilderAPI_Transform
from OCP.BRepMesh import BRepMesh_IncrementalMesh
BASE = r"E:\car_projects\cad_solidcraft\exports"
sh = import_step(r"E:\car_projects\freecad\models\LubanCat 5-外壳3D文件-20240911.STEP")
t = gp_Trsf()
t.SetValues(1,0,0,0, 0,0,-1,-50, 0,1,0,70.6)
wshape = BRepBuilderAPI_Transform(sh.wrapped, t, True).Shape()
BRepMesh_IncrementalMesh(wshape, 0.2, False, 0.5, True)
w = StlAPI_Writer()
w.ASCIIMode = False
print("write:", w.Write(wshape, BASE + r"\CAT_shell_stl.stl"))
from OCP.TopExp import TopExp_Explorer
from OCP.TopAbs import TopAbs_SOLID
n = 0
ex = TopExp_Explorer(wshape, TopAbs_SOLID)
while ex.More(): n += 1; ex.Next()
print("solids:", n)
