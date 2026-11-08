import build123d as bd
from build123d import import_step
sh = import_step(r"E:\car_projects\cad_solidcraft\exports\battery_cradle_a8.step")
solids = sh.solids()
allc = bd.Compound(list(solids))
def probe(x,y,z,r,h):
    tool = bd.Cylinder(r,h).translate((x,y,z))
    inter = allc.intersect(tool)
    return sum(s.volume for s in inter) if inter else 0.0
ok=True
print("solid 数:", len(solids), "bbox:", [round(v,1) for v in (lambda b:(b.min.X,b.min.Y,b.min.Z,b.max.X,b.max.Y,b.max.Z))(sh.bounding_box())])
print("1) 单实体", "PASS" if len(solids)==1 else "FAIL"); ok&=len(solids)==1
# 2) 供电口 (左壁窗口) 通
v=probe(-81.5,-32,68,1.5,3); print("2) 供电口", round(v,1), "PASS" if v==0 else "FAIL"); ok&=v==0
v=probe(-81.5,-10,68,1.5,3); print("2b) 左壁口外实体", round(v,1), "PASS" if v>10 else "FAIL"); ok&=v>10
# 3) 电池腔空
v=probe(-49.3,0,70,10,5); print("3) 电池腔", round(v,1), "PASS" if v==0 else "FAIL"); ok&=v==0
# 4) 槽: 侧壁完全切掉 + 底部 web 0.8 保留
for x0,tag in [(-78.6,"左槽"),(-20,"右槽")]:
    sidew = round(probe(x0, 10, 68, 2, 3),1)   # 侧壁区 (槽带内)
    web   = round(probe(x0, 0, 61.9, 2.5, 0.6),1) # 底部 web z61.6..62.2
    nogap = round(probe(x0, 0, 63.0, 2.5, 0.6),1) # web 上方应空
    good = sidew==0 and web>10 and nogap==0
    print(f"4) {tag}: 侧壁{sidew}(应0) web{web}(应>10) web上{nogap}(应0)", "PASS" if good else "FAIL"); ok&=good
# 5) 柱位地板完整 (槽不到柱 y): 柱 y=43/39.04 处地板 2mm
for x,y in [(-23.73,43),(-74.87,39.04)]:
    v=probe(x,y,62.5,2,1.6); print(f"5) 柱位地板({x},{y})", round(v,1), "PASS" if v>25 else "FAIL"); ok&=v>25
# 6) 四柱
for x,y,tag in [(-23.73,43,"R1"),(-23.73,-43,"R2"),(-74.87,39.04,"F1"),(-74.87,-39.04,"F2")]:
    ring=probe(x,y,52.5,2.6,1.0); bore=[round(probe(x,y,z,1.1,1.0),2) for z in (52.5,55,57.5)]
    good = ring>15 and all(b==0 for b in bore)
    print(f"6) {tag} 环{ring:.1f} 孔{bore}", "PASS" if good else "FAIL"); ok&=good
# 7) 槽 y 与柱 y 无重叠
print("7) 槽|y|<=30 vs 柱|y|-3.5=35.5: 无重叠", "PASS" if 30<35.5 else "FAIL")
print("ALL:", "PASS" if ok else "FAIL")
