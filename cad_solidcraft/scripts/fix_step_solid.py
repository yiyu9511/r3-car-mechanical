import build123d as bd
from build123d import import_step
from OCP.BRepBuilderAPI import BRepBuilderAPI_Sewing, BRepBuilderAPI_MakeSolid
from OCP.TopExp import TopExp_Explorer
from OCP.TopAbs import TopAbs_SHELL, TopAbs_SOLID
from OCP.STEPControl import STEPControl_Writer, STEPControl_StepModelType
from OCP.Interface import Interface_Static
from OCP.IFSelect import IFSelect_ReturnStatus

sh = import_step(r"E:\car_projects\cad_solidcraft\exports\battery_cradle.step")
print("input solids:", len(sh.solids()), "faces:", len(sh.faces()))
# 缝合
sew = BRepBuilderAPI_Sewing(1e-4, True, True, True, False)
for f in sh.faces():
    sew.Add(f.wrapped)
sew.Perform()
sewn = sew.SewedShape()
# 找闭合壳
solids = []
ex = TopExp_Explorer(sewn, TopAbs_SHELL)
while ex.More():
    shell = ex.Current()
    try:
        ms = BRepBuilderAPI_MakeSolid(shell)
        if ms.IsDone():
            solids.append(ms.Solid())
    except Exception as e:
        print("shell->solid skip:", e)
    ex.Next()
print("repaired solids:", len(solids))
if solids:
    out = bd.Compound([bd.Solid(s) for s in solids])
    Interface_Static.SetCVal_s("write.step.schema", "AP214")
    w = STEPControl_Writer()
    w.Transfer(out.wrapped, STEPControl_StepModelType.STEPControl_AsIs)
    r = w.Write(r"E:\car_projects\cad_solidcraft\exports\battery_cradle.step")
    print("write:", r)
    sh2 = import_step(r"E:\car_projects\cad_solidcraft\exports\battery_cradle.step")
    print("re-import solids:", len(sh2.solids()), "vol:", round(sum(s.volume for s in sh2.solids())))
