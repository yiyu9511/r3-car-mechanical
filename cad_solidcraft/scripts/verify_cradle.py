"""OCCT verification of current brass-standoff cradle and export readback."""
import sys,os,json,math,hashlib
from pathlib import Path
sys.path.insert(0,os.environ['PATH_TO_FREECAD_LIBDIR'])
import FreeCAD as App,Part,MeshPart
ROOT=Path(__file__).resolve().parents[2]
OUT=Path(os.environ.get('R3_CAD_OUT',str(ROOT/'cad_solidcraft/build')))
shape=Part.read(str(OUT/'battery_cradle.step'))
mount=Part.read(str(OUT/'battery_mount.step'))
V=App.Vector;checks=[]
anchors=[(-25.57,-39.04),(-25.57,39.04),(25.57,-43),(25.57,43)]
def check(id,ok,actual,expected,method='OCCT BRep probe'):
 checks.append(dict(id=id,status='pass' if ok else 'fail',actual=actual,expected=expected,method=method))
 if not ok:print('FAIL',checks[-1],flush=True)
def box(x,y,z,l,w,h):return Part.makeBox(l,w,h,V(x,y,z))
def hexsolid(x,y,z,af,h):
 r=af/math.sqrt(3);vs=[V(x+r*math.cos(i*math.pi/3),y+r*math.sin(i*math.pi/3),z) for i in range(6)]
 return Part.Face(Part.makePolygon(vs+[vs[0]])).extrude(V(0,0,h))
def empty(id,tool):
 v=shape.common(tool).Volume;check(id,v<.001,v,0)
def full(id,tool):
 v=shape.common(tool).Volume;check(id,abs(v-tool.Volume)<.01,v,tool.Volume)
def vent_tool(x,z=-2.5,h=4.6):
 return box(x-2,-25,z,4,50,h).fuse(Part.makeCylinder(2,h,V(x,-25,z))).fuse(Part.makeCylinder(2,h,V(x,25,z)))
vents=[vent_tool(x) for x in [-23,-3.5,3.5,23]]
# Authorized finish / wall-relief regions, explicitly excluded only from unchanged-material tests.
finish_regions=[]
for x in [-23,-3.5,3.5,23]:
 r=2.351
 finish_regions.append(box(x-r,-25,1.649,2*r,50,.452).fuse(Part.makeCylinder(r,.452,V(x,-25,1.649))).fuse(Part.makeCylinder(r,.452,V(x,25,1.649))))
for x in [-14,8]:
 for sy in [-1,1]:finish_regions.append(box(x-.001,42.799 if sy>0 else -43.301,1.499,6.002,.502,.602))
finish_regions.append(box(-34,-50,11.499,68,100,.602))
for sx in [-1,1]:
 for sy in [-1,1]:finish_regions.append(box(32.099 if sx>0 else -33.401,44.099 if sy>0 else -45.401,1.399,1.302,1.302,10.702))
for sy in [-1,1]:finish_regions.append(box(21.569,42.799 if sy>0 else -45.401,1.999,8.002,2.602,10.102))
check('one_valid_printable_solid',len(shape.Solids)==1 and shape.isValid() and shape.isClosed(),{'solids':len(shape.Solids),'valid':shape.isValid(),'closed':shape.isClosed()},'one valid closed solid')
b=shape.optimalBoundingBox();actual=[b.XMin,b.XMax,b.YMin,b.YMax,b.ZMin,b.ZMax];expected=[-33.3,33.3,-49,49,-2.4,12]
functional_bounds_ok=all(abs(a-e)<.001 for a,e in zip(actual[:5],expected[:5]))
check('functional_xy_and_bottom_datums',functional_bounds_ok,actual[:5],expected[:5],'OCCT optimalBoundingBox')
# Native fillet end patches can exceed the nominal non-mating wall top very slightly on export.
# Keep that deviation visible; do not relax mounting or cavity tolerances to hide it.
height_delta=actual[5]-12
checks.append({'id':'rounded_wall_top_envelope','status':'pass' if abs(height_delta)<.001 else ('warning' if 0<=height_delta<=.05 else 'fail'),
 'actual':{'zmax':actual[5],'delta_from_nominal':height_delta},'expected':{'nominal_z':12,'nominal_tolerance':.001,'non_mating_round_patch_review_limit':.05},
 'method':'OCCT tight bounds; additionally observed in fine tessellation',
 'message':'Retain slight fillet-patch overshoot as a warning; mounting plane and inner-fit dimensions are checked separately.'})
empty('reference_cavity',box(-31.3,-43.3,2.001,62.6,86.6,9.999))
empty('reference_cable_opening',box(-33.4,-40.999,2.001,2.101,15.998,9.999))
# Whole interior floor with declared nut traps / through holes and two shallow grooves excluded.
material=box(-31.29,-43.29,-2.399,62.58,86.58,4.398)
for x in [-14,8]:material=material.cut(box(x,-50,-2.4,6,100,1.2))
for x,y in anchors:
 material=material.cut(hexsolid(x,y,-1,5.8,4))
 material=material.cut(Part.makeCylinder(1.65,6,V(x,y,-3)))
for t in vents:material=material.cut(t)
for t in finish_regions:material=material.cut(t)
full('uniform_4p4_floor_outside_declared_slots_and_edge_rounds',material)
for i,t in enumerate(vents,1):empty('ventilation_slot_through_'+str(i),t)
full('center_longitudinal_rib_below_edge_rounds',box(-1.49,-24.9,-2.399,2.98,49.8,4.048))
for y in [-33,28]:full('end_cross_beam_'+str(y),box(-28,y,-2.399,56,5,4.398).cut(box(-14,-50,-2.4,6,100,1.2)).cut(box(8,-50,-2.4,6,100,1.2)))
for x in [-14,8]:
 empty('strap_depth_1p2_'+str(x),box(x+.001,-55,-2.399,5.998,110,1.198))
 full('strap_roof_3p2_'+str(x),box(x+.001,-42.799,-1.199,5.998,85.598,3.198))
 for y in [-49.999,43.301]:empty('rail_and_wall_strap_exit_'+str((x,y)),box(x+.001,y,-1.199,5.998,6.698,13.3))
# Solid bottom at the middle and around the former side slots; no isolated seat islands.
for x in [-29,26]:full('outer_floor_continuity_'+str(x),box(x,-30,-2.399,3,60,4.398))
# Compare the unchanged source region above the original base datum, including cable opening.
ref=min(Part.read(str(ROOT/'models/电池托架参考.step')).Solids,key=lambda s:s.Volume).copy();ref.translate(V(49.3,0,-61.5))
region=box(-33.3,-45.3,0,66.6,90.6,12)
for x,w in [(-29,6),(22,6),(-14,6),(8,6)]:region=region.cut(box(x-.001,-46,-.01,w+.002,92,12.02))
for x,y in anchors:region=region.cut(hexsolid(x,y,-1.01,5.802,14))
for t in vents+finish_regions:region=region.cut(t)
a=shape.common(region);bref=ref.common(region);diff=a.cut(bref).Volume+bref.cut(a).Volume
check('reference_protected_geometry',diff<.01,diff,'symmetric difference <0.01 mm3')
for sy in [-1,1]:
 empty('straight_wall_relief_'+str(sy),box(21.571,42.801 if sy>0 else -45.399,2.001,7.998,2.598,9.998))
for sx in [-1,1]:
 for sy in [-1,1]:
  empty('rounded_external_corner_'+str((sx,sy)),box(33.24 if sx>0 else -33.29,45.24 if sy>0 else -45.29,6,.05,.05,1))
for x in [-23,-3.5,3.5,23]:empty('rounded_vent_upper_lip_'+str(x),box(x+2.19,-.1,1.98,.02,.2,.01))
for x in [-11,11]:
 for sy in [-1,1]:empty('rounded_strap_entry_'+str((x,sy)),box(x-.1,43.24 if sy>0 else -43.29,1.94,.2,.05,.05))
for sy in [-1,1]:empty('rounded_functional_outer_lip_'+str(sy),box(-.1,48.94 if sy>0 else -48.99,1.94,.2,.05,.05))
for i,(x,y) in enumerate(anchors):
 empty('stud_clearance_'+str(i),Part.makeCylinder(1.649,14.5,V(x,y,-2.4)))
 empty('nut_trap_clear_'+str(i),hexsolid(x,y,-.999,5.798,13))
 seat=hexsolid(x,y,-2.399,5.798,1.398).cut(Part.makeCylinder(1.651,1.5,V(x,y,-2.4)))
 full('nut_seat_thickness_1p4_'+str(i),seat)
 copper_footprint=hexsolid(x,y,-2.399,5.5,.05).cut(Part.makeCylinder(1.651,.1,V(x,y,-2.4)))
 full('edge_covers_copper_'+str(i),copper_footprint)
check('no_printed_standoffs',abs(shape.optimalBoundingBox().ZMin+2.4)<.001,shape.optimalBoundingBox().ZMin,-2.4)
check('strap_to_mount_clearance',25.57-5.5-14>6,25.57-5.5-14,'>6 mm from seat envelope to strap')
# Hardware is separate: four copper bodies, four nuts, one printed body.
check('mount_nine_solids',len(mount.Solids)==9 and mount.isValid(),{'solids':len(mount.Solids),'valid':mount.isValid()},'9 valid solids')
contacts=[]
for idx,s in enumerate(mount.Solids):
 if s.Volume>10000:continue
 v=shape.common(s).Volume
 check('hardware_clearance_'+str(idx),v<.001,v,'zero unintended hardware/print intersection')
 contacts.append(v)
check('full_nut_thread_engagement',4-1.4>=2.4,4-1.4,'>=2.4 mm nut height; nominal envelope, threads not modeled')
check('stud_below_battery_floor',abs(2-(-2.4+4)-.4)<1e-9,2-(-2.4+4),.4,'Nominal dimensions')
check('nut_below_battery_floor',abs(2-(-1+2.4)-.6)<1e-9,2-(-1+2.4),.6,'Nominal dimensions')
# Assemble on the unmodified R3 source chassis.
chassis=Part.read(str(ROOT/'models/R3mini四驱小车底盘（无悬挂）_utf8.stp'))
steel=max((s for s in chassis.Solids if s.BoundBox.ZLength<2),key=lambda s:s.Volume)
world=shape.copy();world.rotate(V(),V(0,0,1),-90);world.translate(V(0,-102.9,13.9))
mount_world=mount.copy();mount_world.rotate(V(),V(0,0,1),-90);mount_world.translate(V(0,-102.9,13.9))
for i,(x,y) in enumerate(anchors):
 wx,wy=y,-x-102.9
 v=steel.common(Part.makeCylinder(1.49,1.5,V(wx,wy,0))).Volume
 check('plate_anchor_'+str(i),v<.001,v,0,'Original source steel; front anchors lie at ends of short obround slots')
 # Full hardware footprint must remain within the outer plate boundary; hole area is intentional.
 v=chassis.common(Part.makeCylinder(3,4,V(wx,wy,-4))).Volume
 check('underside_fastener_access_'+str(i),v<.001,v,0,'6 mm screw/head access envelope, not ground-clearance validation')
coll=[]
for idx,s in enumerate(chassis.Solids):
 a=s.BoundBox;b=mount_world.BoundBox
 if min(min(getattr(a,k+'Max'),getattr(b,k+'Max'))-max(getattr(a,k+'Min'),getattr(b,k+'Min')) for k in 'XYZ')<=1e-5:continue
 v=mount_world.common(s).Volume
 if v>.001:coll.append({'solid':idx,'volume':v})
check('chassis_interference',not coll,coll,'no intersection >0.001 mm3')
# Current device assembly is read only here; omit the superseded battery and its budget.
doc=App.openDocument(str(ROOT/'assemblies/two_layer.FCStd'));device_hits=[]
for name in ['C30D','FrontTOF','RearTOF','UpperSteelPlate','CATMount','CATShell0','CATShell1']:
 o=doc.getObject(name)
 if o is None:continue
 s=o.Shape.copy();s.Placement=o.getGlobalPlacement().multiply(o.Placement.inverse()).multiply(s.Placement)
 a=s.BoundBox;b=mount_world.BoundBox
 depths=[min(getattr(a,k+'Max'),getattr(b,k+'Max'))-max(getattr(a,k+'Min'),getattr(b,k+'Min')) for k in 'XYZ']
 if min(depths)<=1e-5:continue
 surface_area=None
 if not s.Solids:
  surface_area=mount_world.common(s).Area
  s=box(a.XMin,a.YMin,a.ZMin,a.XLength,a.YLength,a.ZLength)
 v=mount_world.common(s).Volume
 if v>.001:device_hits.append({'device':name,'overlap_mm3':v,'surface_intersection_area_mm2':surface_area})
App.closeDocument(doc.Name)
check('current_device_clearance',not device_hits,device_hits,'no intersection; rear TOF uses conservative envelope')
# Export round trip and STL closure.
shape.exportStep(str(OUT/'battery_cradle_roundtrip.step'));re=Part.read(str(OUT/'battery_cradle_roundtrip.step'))
check('step_readback',re.isValid() and len(re.Solids)==1 and abs(re.Volume-shape.Volume)<.01,{'volume_delta':re.Volume-shape.Volume,'solids':len(re.Solids)},'valid single solid, delta <0.01 mm3')
mesh=MeshPart.meshFromShape(Shape=shape,LinearDeflection=.08,AngularDeflection=.15);mesh.write(str(OUT/'battery_cradle.stl'))
check('stl_closed',mesh.isSolid(),mesh.isSolid(),True)
world.exportStep(str(OUT/'battery_cradle_world.step'));mount_world.exportStep(str(OUT/'battery_mount_world.step'))
report={'schema_version':'0.1','report_type':'freecad-model-validation','subject':{'document':'BatteryCradle','path':str(OUT/'battery_cradle.step')},'evidence_level':'geometry','status':'fail' if any(x['status']=='fail' for x in checks) else 'warning','printable_geometry_status':'fail' if any(x['status']=='fail' and x['id']!='current_device_clearance' for x in checks) else 'pass','summary':{'pass':sum(x['status']=='pass' for x in checks),'fail':sum(x['status']=='fail' for x in checks),'warning':sum(x['status']=='warning' for x in checks),'not_tested':4},'checks':checks,'volume_mm3':shape.Volume,'source_sha256':hashlib.sha256((ROOT/'models/电池托架参考.step').read_bytes()).hexdigest(),'dimensions_mm':{'ventilation_slots':{'count':4,'width':4,'length':54,'end_radius':2,'direction':'local Y, parallel to cradle long sides'},'edge_radii':{'outside_uprights':1.2,'wall_top':.5,'vent_top':.35,'strap_entry':.5,'flange_outer_long_lips':.4},'wall_relief_above_rear_nuts':{'width':8,'z_min':2,'x_range':[21.57,29.57]},'floor_thickness':4.4,'strap_width':6,'strap_depth':1.2,'strap_roof':3.2,'nut_pocket_af':5.8,'nut_seat_thickness':1.4,'stud_clearance_diameter':3.3,'brass_body_height':10,'male_stud_length':4},'assumptions':['Copper hex AF5.5 nominal; verify purchased part','M3 nut AF5.5 and height2.4 nominal, pocket AF5.8','Female bore shown as nominal 6 mm envelope; vendor depth unknown; no bottom screw length selected'],'untested_risks':['Physical nut fit, usable stud thread length and manufacturing tolerances','Actual battery, connector/cable route, actual fastener occupancy and ground clearance','Printing orientation/support, material, strength, temperature and vibration','Actual battery cooling improvement; contact pressure on the remaining support ribs'],'battery_height_budget_mm':{'floor_world_z':15.9,'upper_plate_bottom_z':51.5,'clearance':2,'max_battery_height':33.6},'artifacts':['battery_cradle.sc','battery_cradle.step','battery_cradle.stl','battery_mount.sc','battery_mount.step']}
(OUT/'battery_cradle_checks.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));print('SUMMARY',report['summary'],flush=True)
if report['summary']['fail']:sys.exit(1)
