import build123d as bd
from build123d import import_step
sh = import_step(r"E:\car_projects\cad_solidcraft\exports\battery_cradle.step")
allc = bd.Compound(list(sh.solids()))
def probe(x,y,z,r,h):
    tool=bd.Cylinder(r,h).translate((x,y,z)); inter=allc.intersect(tool)
    return sum(s.volume for s in inter) if inter else 0.0
print("1) 中槽 Y 全贯通检查:")
bad=[]
for x in (-59,-39):
    for y in range(-44,45,2):
        if probe(x,y,62.0,0.8,1.0)>0.05: bad.append((x,y))
print("   有料位置:", bad if bad else "无 → 两条槽全程贯通 PASS")
print("2) web 保留 z63.0:", round(probe(-59,0,63.0,1.0,0.6),2), round(probe(-39,0,63.0,1.0,0.6),2), "(应>0)")
print("3) 柱未被槽切: 柱位 z62.0:", round(probe(-74.87,39.04,62.0,2.0,0.8),2), round(probe(-23.73,43,62.0,2.0,0.8),2), "(应>8)")
print("4) 槽外地板完整 z62.0:", round(probe(-49.3,0,62.0,1.5,0.8),2), "(应≈2.8)")
print("5) 端壁底部被槽切穿 z62.0:", round(probe(-59,44.0,62.0,1.5,0.8),2), "(应≈0)")
print("6) 柱孔贯通:", all(probe(-23.73,43,z,1.0,1.0)<0.05 for z in (53,55,57)))
print("vol:", round(sum(s.volume for s in sh.solids())), "bbox:", [round(v,1) for v in (lambda b:(b.min.X,b.min.Y,b.min.Z,b.max.X,b.max.Y,b.max.Z))(sh.bounding_box())])
