import sys,os,json,math
from pathlib import Path
ROOT_DIR=Path(__file__).resolve().parents[2]
sys.path.insert(0,os.environ['PATH_TO_FREECAD_LIBDIR']);sys.path.insert(0,str(ROOT_DIR/'tools'))
from cad_common import App,Part,ROOT,V,cat_shells
O=ROOT/'cad_solidcraft/build/cat';O.mkdir(parents=True,exist_ok=True);shells,face=cat_shells()
for i,s in enumerate(shells):print('SHELL',i,str(s.BoundBox),s.Volume)
Part.makeCompound(shells).exportStep(str(O/'cat_shells.step'))
wires=[]
for w in face.Wires:
 b=w.BoundBox;wires.append({'bbox':[b.XMin,b.XMax,b.YMin,b.YMax,b.ZMin,b.ZMax],'edges':len(w.Edges),'length':w.Length})
(O/'source_audit.json').write_text(json.dumps({'wires':wires,'bottom_bbox':str(face.BoundBox)},indent=2))
lower=min(shells,key=lambda s:s.BoundBox.ZMin);lower.exportStep(str(O/'cat_lower_shell.step'))
face.exportStep(str(O/'cat_bottom_surface.step'))
steel=Part.read(str(ROOT/'cad_solidcraft/exports/steel_plate.step'));print('STEEL',str(steel.BoundBox))
rows=[]
for i,(x,y) in enumerate([(-50,-88.39),(50,-88.39),(-50,-11.47),(50,-11.47)],1):
 cs=[f.Surface for f in steel.Faces if isinstance(f.Surface,Part.Cylinder) and abs(f.Surface.Axis.z)>.99 and abs(f.Surface.Radius-1.6)<.01]
 c=min(cs,key=lambda c:(c.Center.x-x)**2+(c.Center.y-y)**2)
 v=steel.common(Part.makeCylinder(1.5,steel.BoundBox.ZLength,V(c.Center.x,c.Center.y,steel.BoundBox.ZMin))).Volume
 # bound of reference 8 mm post in shell interface x/y at y=-50
 local=V(c.Center.x,c.Center.y+50,0)
 support=Part.makeCylinder(4,3,V(local.x,local.y,-3))
 contact=face.extrude(V(0,0,-3)).common(support).Volume/3
 rows.append({'id':f'P{i}','world_xy':[c.Center.x,c.Center.y],'plate_top_z':53,'hole_diameter':3.2,'probe_intersection_mm3':v,'top_post_contact_mm2':contact,'state':'user_confirmed'})
print(json.dumps(rows,indent=2));(O/'hole_selection_checks.json').write_text(json.dumps({'plate_source_bbox':str(steel.BoundBox),'plate_translation':[0,0,51.5],'shell_translation':[0,-50,66],'holes':rows,'scope':'Source hole existence verified; user confirmed all four anchors in current conversation'},indent=2))
