# 电池托架 v10 数值验证
import build123d as bd, sys
from build123d import import_step
sh = import_step(r"E:\car_projects\cad_solidcraft\exports\battery_cradle.step")
solids=list(sh.solids())
allc=bd.Compound(solids)
def probe(x,y,z,r,h):
    tool=bd.Cylinder(r,h).translate((x,y,z)); inter=allc.intersect(tool)
    return sum(s.volume for s in inter) if inter else 0.0
ok=True
def check(name, cond, detail=""):
    global ok
    print(("PASS " if cond else "FAIL ")+name, detail)
    ok = ok and cond
check("单实体", len(solids)==1, f"solids={len(solids)}")
check("柱周实心(后)", probe(-22.3,39.09,62.5,1.0,1.8)>1.5)
check("柱周实心(前)", probe(-76.3,35.63,62.5,1.0,1.8)>1.5)
check("蜂窝贯通(远)", probe(-52.3,0,62.5,1.0,1.8)<0.05)
check("蜂窝壁保留", probe(-73.3,-38.9,62.5,0.5,1.8)>0.3)
check("槽内底部空", probe(-59,0,61.9,0.8,0.5)<0.05)
check("槽 web 保留", probe(-59,0,63.0,1.0,0.6)>0.5)
check("底板未整体切穿", probe(-49.3,0,62.5,1.5,0.8)>2.0)
check("端壁窗口切穿", probe(-59,44.5,68,1.5,2.0)<0.05)
check("窗口外端壁保留", probe(-49,44,68,1.5,2.0)>5)
check("长侧壁保留", probe(-81.5,0,68,1.0,2.0)>2)
check("Ø14 法兰", probe(-23.73,46.5,52.5,1.0,1.0)>1)
check("加强筋", probe(-23.73+6,43,58,0.9,1.5)>0.5)
check("自攻孔贯通", probe(-23.73,43,55,1.0,1.0)<0.05)
b=sh.bounding_box()
check("bbox 无外扩", abs(b.min.X+82.6)<0.1 and abs(b.max.X+16)<0.1 and abs(b.max.Y-50.0)<0.1)
print("vol:", round(sum(s.volume for s in solids)))
print("ALL:", "PASS" if ok else "FAIL")
sys.exit(0 if ok else 1)
