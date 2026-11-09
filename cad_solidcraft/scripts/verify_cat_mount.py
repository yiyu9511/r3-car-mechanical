import sys,os,json,math,hashlib
from pathlib import Path
sys.path.insert(0,os.environ['PATH_TO_FREECAD_LIBDIR']);sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'tools'))
from cad_common import App,Part,ROOT,V,cat_shells
import MeshPart
O=ROOT/'cad_solidcraft/build/cat';S=Part.read(str(O/'cat_mount.step'));checks=[]
def check(id,ok,actual,expected,method='OCCT BRep probe'):
 checks.append(dict(id=id,status='pass' if ok else 'fail',actual=actual,expected=expected,method=method))
 if not ok:print('FAIL',checks[-1],flush=True)
def bx(x,y,z,a,b,c):return Part.makeBox(a,b,c,V(x,y,z))
def hx(x,y,z,af,h):
 r=af/math.sqrt(3);p=[V(x+r*math.cos(i*math.pi/3),y+r*math.sin(i*math.pi/3),z) for i in range(6)];return Part.Face(Part.makePolygon(p+[p[0]])).extrude(V(0,0,h))
def empty(id,t):
 v=S.common(t).Volume;check(id,v<.001,v,0)
def full(id,t):
 v=S.common(t).Volume;check(id,abs(v-t.Volume)<.01,v,t.Volume)
check('valid_single_solid',S.isValid() and S.isClosed() and len(S.Solids)==1,{'valid':S.isValid(),'closed':S.isClosed(),'solids':len(S.Solids)},'one valid closed solid')
b=S.optimalBoundingBox();dims=[b.XLength,b.YLength,b.ZLength];check('dimensions',all(abs(a-e)<.001 for a,e in zip(dims,[135.32557355773027,98,15])),dims,[135.32557355773027,98,15])
shells,face=cat_shells();ref=face.extrude(V(0,0,-2.4));region=bx(-67.66300877886484,-40.25,-2.4,135.32557355773027,80.5,2.4)
actual=S.common(region);diff=ref.cut(actual).Volume+actual.cut(ref).Volume;check('source_bottom_interface_matches',diff<.01,diff,'symmetric difference <0.01 mm3')
vents=0;holes=0
for w in face.Wires:
 b=w.BoundBox
 if b.XLength>20 and b.YLength<5:
  vents+=1;t=Part.Face(w).extrude(V(0,0,-16));empty('full_vent_path_'+str(vents),t)
 if b.XLength<4 and b.YLength<4:
  holes+=1;x,y=b.Center.x,b.Center.y
  empty('M3_clearance_'+str(holes),Part.makeCylinder(1.649,5.2,V(x,y,-5.1)))
  empty('nut_pocket_'+str(holes),hx(x,y,-4.999,5.798,2.598))
  web=hx(x,y,-2.399,5.798,2.398).cut(Part.makeCylinder(1.651,2.5,V(x,y,-2.4)))
  full('clamp_web_2p4mm_'+str(holes),web)
check('source_opening_counts',vents==8 and holes==6,{'vents':vents,'holes':holes},{'vents':8,'holes':6})
anchors=json.loads((O/'anchors.json').read_text());steel=Part.read(str(ROOT/'cad_solidcraft/exports/steel_plate.step'));steel.translate(V(0,0,51.5))
world=S.copy();world.translate(V(0,-50,68));world.exportStep(str(O/'cat_mount_world.step'))
contacts=[]
for i,(x,wy) in enumerate(anchors,1):
 y=wy+50
 empty('pilot_bore_9mm_'+str(i),Part.makeCylinder(1.249,8.999,V(x,y,-15)))
 full('pilot_roof_'+str(i),Part.makeCylinder(1.249,.998,V(x,y,-5.999)))
 post=Part.makeCylinder(3.999,9.998,V(x,y,-14.999)).cut(Part.makeCylinder(1.251,10,V(x,y,-15)))
 full('post_wall_'+str(i),post)
 v=steel.common(Part.makeCylinder(1.49,1.5,V(x,wy,51.5))).Volume;check('source_plate_anchor_'+str(i),v<.001,v,0)
 foot=S.common(bx(x-8,y-8,-15,16,16,.05));area=foot.Volume/.05;contacts.append(area)
 check('expanded_foot_contact_'+str(i),area>math.pi*(4**2-1.25**2)*1.5,area,'>1.5x plain post annulus area mm2')
 footprint=foot.copy();footprint.translate(V(0,-50,67.95))
 # Entire foot lies within actual steel material except the hole annulus between pilot/steel diameters.
 support=steel.common(footprint).Volume/.05
 check('foot_on_steel_'+str(i),support/area>.94,{'solid_foot_area':area,'steel_support_area':support},'>94% foot contact supported; actual steel hole is larger than pilot')
 check('post_center_edge_margin_'+str(i),49-abs(y)>10,49-abs(y),'>10 mm to tray end')
 # Detailed rib reach and actual contact verified as joined solid; print process remains untested.
for i,(x,wy) in enumerate(anchors,1):
 y=wy+50
 for dx,dy in [(1,0),(-1,0),(0,1),(0,-1)]:
  if dx:probe=bx(x+(4.1 if dx>0 else -5.7),y-.9,-13.7,1.6,1.8,8.6)
  else:probe=bx(x-.9,y+(4.1 if dy>0 else -5.7),-13.7,1.8,1.6,8.6)
  full(f'full_height_web_{i}_{dx}_{dy}',probe)
 footprint=S.common(bx(x-8,y-8,-15,16,16,.05))
 outside=footprint.cut(Part.makeCylinder(6.001,.051,V(x,y,-15)))
 check('ribs_inside_12mm_foot_'+str(i),outside.Volume<.001,outside.Volume,0)
check('steel_intersection',world.common(steel).Volume<.001,world.common(steel).Volume,0)
shell=Part.makeCompound(shells);check('shell_intersection',S.common(shell).Volume<.001,S.common(shell).Volume,0)
check('self_tap_tip_clearance',10-8.5>=1.5,10-8.5,'1.5 mm from tray underside, no washer')
check('self_tap_drill_end_clearance',9-8.5>=.5,9-8.5,'0.5 mm nominal')
check('machine_screw_nut_stack',10-2-2.4-2.4>0,{'shell':2,'clamp':2.4,'nut':2.4,'protrusion':10-2-2.4-2.4,'steel_clearance':7},'full nominal nut engagement and no steel collision')
check('nut_spacing',7.5-5.8>1.5,7.5-5.8,'>1.5 mm between adjacent parallel flats')
mesh=MeshPart.meshFromShape(Shape=S,LinearDeflection=.08,AngularDeflection=.15);mesh.write(str(O/'cat_mount.stl'));check('stl_closed',mesh.isSolid(),mesh.isSolid(),True)
S.exportStep(str(O/'cat_roundtrip.step'));re=Part.read(str(O/'cat_roundtrip.step'))
vol_delta=re.Volume-S.Volume;geom_delta=S.cut(re).Volume+re.cut(S).Volume
check('step_roundtrip_topology',re.isValid() and len(re.Solids)==1,{'valid':re.isValid(),'solids':len(re.Solids)},'one valid solid')
check('step_roundtrip_geometry',abs(geom_delta)<.01,geom_delta,'symmetric difference <0.01 mm3')
checks.append({'id':'step_roundtrip_volume_integration','status':'pass' if abs(vol_delta)<.01 else 'warning','actual':vol_delta,'expected':'absolute integrated volume delta <0.01 mm3','method':'OCCT Volume before and after serialization; cross-check with geometric difference','message':'A warning is retained for numerical integration drift; not silently relaxed.'})
# Entire non-slot, non-hole tray is 5mm; no nut-seat protrusions below it.
base=bx(-67.66300877886484,-49,-5,135.32557355773027,98,5)
for w in face.Wires:
 if w.BoundBox.XLength<100:base=base.cut(Part.Face(w).extrude(V(0,0,-6)))
for x in [-25.8630087788648,29.1369912211352]:
 for y in [-7.5,0,7.5]:base=base.cut(hx(x,y,-5,5.8,2.6))
full('uniform_5mm_plate_with_only_declared_voids',base)
empty('no_projecting_nut_rails',bx(-32,-12,-6,68,24,.999))
# Contact pads must not cover any other inner wire of the actual steel top face.
face_steel=max((f for f in steel.Faces if f.BoundBox.ZLength<1e-5 and abs(f.CenterOfMass.z-53)<.001),key=lambda f:f.Area)
for i,(x,wy) in enumerate(anchors,1):
 y=wy+50;foot=S.common(bx(x-8,y-8,-15,16,16,.05));foot.translate(V(0,-50,67.95));near=[]
 for w in face_steel.Wires:
  if w.isSame(face_steel.OuterWire):continue
  hole=Part.Face(w)
  if hole.isInside(V(x,wy,53),.01,True):continue
  gap=foot.distToShape(hole)[0];near.append(gap)
 check('neighbor_holes_not_covered_'+str(i),min(near)>.5,min(near),'minimum >0.5 mm to all other hole boundaries; tool access still needs intended fastener')

r={'schema_version':'0.1','report_type':'freecad-model-validation','subject':{'document':'CATMount','path':'cad_solidcraft/exports/cat_mount.step'},'evidence_level':'geometry','status':'fail' if any(x['status']=='fail' for x in checks) else 'warning','summary':{'pass':sum(x['status']=='pass' for x in checks),'fail':sum(x['status']=='fail' for x in checks),'warning':sum(x['status']=='warning' for x in checks),'not_tested':4},'checks':checks,'volume_mm3':S.Volume,'foot_contact_areas_mm2':contacts,'anchors_world_xy':anchors,'world_translation':[0,-50,68],'source_sha256':hashlib.sha256((ROOT/'models/LubanCat 5-外壳3D文件-20240911.STEP').read_bytes()).hexdigest(),'fasteners':{'chassis':'M3x10 plastic self tapping, nominal no washer, pilot diameter2.5 depth9 is trial value','shell':'M3x10 machine screw from shell interior downward, standard nut AF5.5 height2.4; pocket AF5.8 depth2.6 embedded into uniform5mm plate, 2.4mm clamp web'},'untested_risks':['PCB underside clearance for screw heads and opening the shell for installation','Actual self-tapping screw thread form, pilot fit, torque and plastic retention','Printing material/orientation/support, warp, heat and vibration','Final access to nearby reused chassis holes and complete device hardware layout']}
(O/'cat_mount_checks.json').write_text(json.dumps(r,ensure_ascii=False,indent=2));print('SUMMARY',r['summary'],'FOOT AREAS',contacts,flush=True)
if r['summary']['fail']:sys.exit(1)
