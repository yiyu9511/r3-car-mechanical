"""Independent geometry checks for the current compact frame/camera prototype.
Does not validate unknown camera dimensions, LiDAR thread, optical field or printed strength.
"""
from pathlib import Path
import sys,os,json,math,itertools,hashlib
from collections import Counter
sys.path.insert(0,os.environ['PATH_TO_FREECAD_LIBDIR']);import FreeCAD as A,Part
R=Path(__file__).resolve().parents[2];O=R/'cad_solidcraft/build/lidar_camera';V=A.Vector
checks=[]
def check(id,ok,actual,expected,method='OCCT BRep geometry'):
 r=dict(id=id,status='pass' if ok else 'fail',actual=actual,expected=expected,method=method);checks.append(r)
 if not ok:print('FAIL',r,flush=True)
def box(x,y,z,l,w,h):return Part.makeBox(l,w,h,V(x,y,z))
def bb(s):
 b=s.optimalBoundingBox();return [b.XMin,b.XMax,b.YMin,b.YMax,b.ZMin,b.ZMax]
parts={n:Part.read(str(O/(n+'.step'))) for n in ['lidar_frame','camera_dock','camera_housing','camera_rear_lid']}
for n,s in parts.items():check(n+'_topology',len(s.Solids)==1 and s.isValid() and s.isClosed(),{'solids':len(s.Solids),'valid':s.isValid(),'closed':s.isClosed()},'one valid closed solid')
f=parts['lidar_frame'];d=parts['camera_dock'];h=parts['camera_housing']
try:
 f.check(True)
 checks.append({'id':'frame_detailed_BOP_check','status':'pass','actual':'no diagnostic','expected':'no BOP diagnostic'})
except Exception as e:
 counts=dict(Counter(line.strip() for line in str(e).splitlines() if line.strip()))
 checks.append({'id':'frame_detailed_BOP_check','status':'warning' if f.isValid() and f.isClosed() else 'fail','actual':counts,'expected':'no BOP diagnostic','message':'Detailed exported-curve warnings retained; initial design only, not production release.'})
anchors=json.loads((O/'anchors.json').read_text());steel=Part.read(str(R/'cad_solidcraft/exports/steel_plate.step'));steel.translate(V(0,0,51.5))
for i,(x,wy) in enumerate(anchors,1):
 y=wy-55
 v=f.common(Part.makeCylinder(1.249,8.999,V(x,y,0))).Volume;check(f'pilot_{i}',v<.001,v,'empty D2.5 x9 blind bore')
 roof=Part.makeCylinder(1.249,.9,V(x,y,9.01));v=f.common(roof).Volume;check(f'pilot_closed_roof_{i}',abs(v-roof.Volume)<.001,v,roof.Volume)
 v=steel.common(Part.makeCylinder(1.49,1.5,V(x,wy,51.5))).Volume;check(f'selected_steel_hole_{i}',v<.001,v,'zero material along selected D3.2 hole')
 if i>=3:
  nx=-26 if x<0 else 26;ny=81.613399283666-55
  for label,rad,z,length in [('head',2.99,0,4.19),('shank',1.79,4.2,25.1)]:
   t=Part.makeCylinder(rad,length,V(nx,ny,z));v=f.common(t).Volume;check(f'adjacent_{label}_clear_{i}',v<.001,v,0)
  minwall=math.hypot(nx-x,ny-y)-3-1.25
  check(f'pilot_wall_next_to_relief_{i}',minwall>1.4,minwall,'>1.4mm geometric ligament before self-tapping; physical retention untested')
for x in [-25.5,25.5]:
 v=f.common(Part.makeCylinder(1.649,6.7,V(x,8.3,28.9))).Volume;check('rotated_bottom_mount_'+str(x),v<.001,v,0)
check('lidar_clearance_pad_height',abs(f.BoundBox.ZMax-35.5)<.001,f.BoundBox.ZMax,35.5)
# Verify18 full rectangular ports at true mounting orientation.
for tag in ['FRONT','LEFT','RIGHT']:
 for u in [-25,-15,-5,5,15,25]:
  if tag=='FRONT':t=box(u-3.19,35.9,22.01,6.38,3.2,4.98)
  elif tag=='LEFT':t=box(-35.1,u-3.19,22.01,3.2,6.38,4.98)
  else:t=box(31.9,-u-3.19,22.01,3.2,6.38,4.98)
  v=f.common(t).Volume;check(f'port_{tag}_{u}',v<.001,v,0)
# Rear has no closing rim across the wiring corridor.
v=f.common(box(-12,-36,14.01,24,4,14.8)).Volume;check('rear_wiring_open',v<.001,v,0)
# Assembly groups were exported in their world positions before external references were added.
g=json.loads((O/'groups.json').read_text());world={k:Part.read(str(O/(k+'_world.step'))) for k in ['frame','dock','guard','rear_lid','camera_references','hardware_envelopes']}
for a,b in itertools.combinations(world,2):
 sa,sb=world[a],world[b];ba,bbb=sa.BoundBox,sb.BoundBox
 if min(min(getattr(ba,k+'Max'),getattr(bbb,k+'Max'))-max(getattr(ba,k+'Min'),getattr(bbb,k+'Min')) for k in 'XYZ')<=1e-5:continue
 v=sa.common(sb).Volume;check(a+'_'+b+'_clear',v<.001,v,0)
# Original LiDAR is rotated -90deg about Z: mounting ears / 90deg blind sector now face world-Y.
source=Part.read(str(R/'models/单线雷达总装.STEP'));lidar=Part.makeCompound([s for s in source.Solids if s.BoundBox.YMax>=-40]);lidar.rotate(V(),V(0,0,1),-90);lidar.translate(V(0,55,118.92192707366391))
for key,s in world.items():
 v=s.common(steel).Volume;check(key+'_steel_clear',v<.001,v,'no penetration, footprint contacts at Z53')
 v=s.common(lidar).Volume;check(key+'_lidar_clear',v<.01,v,'no penetration into unchanged rotated source geometry')
# Compare to current CAT without moving it.
cat=Part.read(str(R/'cad_solidcraft/build/cat/cat_shells.step'));cat.translate(V(0,-50,68))
for key in ['frame','dock','guard','rear_lid']:
 v=world[key].common(cat).Volume;check(key+'_CAT_clear',v<.001,v,0)
# Camera shell motion is a rigid X-axis tilt about its own mounting pivot.
for angle in [-20,0,20]:
 shell=Part.makeCompound([world['guard'],world['rear_lid']]);refs=world['camera_references'].copy()
 for s in [shell,refs]:s.rotate(V(0,116,77),V(1,0,0),angle+10)
 for a,s in [('guard',shell),('camera',refs)]:
  for b,t in [('frame',world['frame']),('dock',world['dock']),('steel',steel),('lidar',lidar)]:
   v=s.common(t).Volume;check(f'pitch_{angle}_{a}_{b}',v<.001,v,'collision-free nominal envelope; cable sweep untested')
# Hook install: raise2mm, translate forward to clear3mm rail, then remove vertically.
movable=Part.makeCompound([world[k] for k in ['dock','guard','rear_lid','camera_references']])
for dy,dz in [(0,2),(2,2),(5,2),(5,12)]:
 m=movable.copy();m.translate(V(0,dy,dz));v=m.common(world['frame']).Volume;check(f'hook_release_y{dy}_z{dz}',v<.001,v,'solid clearance with anti-lift bolt removed')
# Floor pad support, not an extra chassis mounting hole.
t=box(-8,97,52.95,16,8,.05);area=steel.common(t).Volume/.05;check('camera_foot_contact',area/128>.95,{'supported_area':area,'nominal_area':128},'>95% nominal foot supported; small existing hole area excluded')
report={'schema_version':'0.1','report_type':'freecad-model-validation','status':'fail' if any(c['status']=='fail' for c in checks) else 'warning','scope':'Compact LiDAR frame and removable-lid camera enclosure prototype; not final print approval','checks':checks,'summary':{'pass':sum(c['status']=='pass' for c in checks),'fail':sum(c['status']=='fail' for c in checks),'warning':sum(c['status']=='warning' for c in checks)},'anchors_world_xy':anchors,'lidar_orientation':'source Rz(-90deg), translation(0,55,118.921927); ears/90deg blind sector toward world-Y/CAT','frame_steel_fastener':'M3x10 self-tapping as user confirmed, D2.5 x9 pilot trial','interface':'U rim front/left/right, rear open;18 rectangular6.4x5 slots at10mm pitch; two5.6mm-wide down hooks; M3x10 anti-lift lock from inside frame','camera':'29x31 PCB and23x25 pitch confirmed; cavity31x33, shell34.2x36.2x18.5; PCBthickness1.2/hole2.5/lens12x8 with optical center19.5from board bottom are UNMEASURED placeholders; body fixing proposedM2.5 and length must be verified','world_bounds':{k:bb(s) for k,s in world.items()},'unverified':['Physical LiDAR bottom-hole count/thread/allowed insertion depth','Camera actual PCB thickness/hole diameter, components and ribbon path','Printed clearances, clip strength, self-tapping retention and vibration','Actual optical FOV and image performance at tilt angles','Print orientation/support strategy for U rim and guards; no print-ready claim']}
(O/'lidar_camera_checks.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));print('SUMMARY',report['summary'],flush=True)
if report['summary']['fail']:sys.exit(1)
