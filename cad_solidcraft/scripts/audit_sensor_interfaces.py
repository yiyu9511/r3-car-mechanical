import sys,os,json,hashlib
from pathlib import Path
sys.path.insert(0,os.environ['PATH_TO_FREECAD_LIBDIR']);import FreeCAD as A,Part
R=Path(__file__).resolve().parents[2];O=R/'cad_solidcraft/build/sensors';O.mkdir(parents=True,exist_ok=True);src=R/'models/单线雷达总装.STEP';S=Part.read(str(src));h=S.Solids[19]
seat=min(s.BoundBox.ZMin for s in S.Solids if s.BoundBox.YMax>=-40);shift=[0,55,86-seat]
checks=[]
def test(id,cond,actual,expected):checks.append({'id':id,'status':'pass' if cond else 'fail','actual':actual,'expected':expected})
def world(v):return [v[i]+shift[i] for i in range(3)]
interfaces=[]
for i,(solid,y) in enumerate([(14,-34.4),(13,34.4)],1):
 t=Part.makeCylinder(2.05,3.2,A.Vector(27.4,y,-13.5),A.Vector(1,0,0));vol=S.common(t).Volume
 test('side_ear_open_'+str(i),vol<1e-6,vol,0)
 point=[30.5,y,-13.5]
 interfaces.append({'id':f'S{i}','kind':'side_ear_through_hole','source_solid':solid,'mouth_source':point,'mouth_world_current':world(point),'axis':[1,0,0],'diameter_mm':4.3,'ear_thickness_mm':3,'hole_pair_pitch_mm':68.8,'thread':'not present; plain through-hole geometry','note':'Existing separate factory ears; inner mounting screws at y=+-25.5 are occupied and are not these outer holes.'})
for i,y in enumerate([-25.5,25.5],1):
 cyl=Part.makeCylinder(1.15,5,A.Vector(-8.3,y,-30.4),A.Vector(0,0,1));v=S.common(cyl).Volume
 stop=Part.makeCylinder(.5,.2,A.Vector(-8.3,y,-24.5))
 test('bottom_bore_clear_'+str(i),v<1e-6,v,0)
 test('bottom_closed_end_'+str(i),h.common(stop).Volume>.1,h.common(stop).Volume,'solid stop beyond drill tip')
 face=h.Faces[118 if y>0 else 122];test('bottom_pad_'+str(i),abs(face.BoundBox.ZMin+30.4)<1e-6,face.BoundBox.ZMin,-30.4)
 point=[-8.3,y,-30.4]
 interfaces.append({'id':f'B{i}','kind':'bottom_blind_bore','mouth_source':point,'mouth_world_current':world(point),'axis':[0,0,1],'modeled_bore_diameter_mm':2.5,'straight_bore_depth_mm':5,'tip_source_z':-24.648924,'nominal_bottom_plane_z':-32.9,'recess_from_bottom_plane_mm':2.5,'hole_pair_pitch_mm':51,'thread':'not modeled; do not infer M2.5 or M3 thread from cylindrical diameter','screw_length':'unknown; obtain actual thread and allowed insertion depth before choosing screw'})
r={'status':'pass' if all(c['status']=='pass' for c in checks) else 'fail','scope':'Read-only source interface audit, not support design or fastener approval','source':str(src.relative_to(R)),'source_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'source_solid_count':len(S.Solids),'source_to_current_world_translation':shift,'lowest_bbox_z':seat,'nominal_bottom_plane_source_z':-32.9,'note':'Current assembly sets entire body bounding-box bottom to Z86; nominal flat housing bottom is ~0.02193mm above that. Side ears lie on source +X, not necessarily vehicle rear (-Y).','interfaces':interfaces,'checks':checks,'camera':{'source':'docs/ref/IMX415_V1R1_尺寸图.png','evidence':'Dimension lines read visually from source drawing; no camera STEP found','pcb_outline_mm':[29,31],'outer_mount_pitch_mm':[23,25],'outer_mount_count':4,'hole_diameter':'not dimensioned in supplied drawing','additional_20mm_pair':'inner lens-holder pair; not treated as PCB-to-support mounting holes','24_mark':'near ribbon connector, not the vertical hole pitch','unverified':['actual camera variant','PCB thickness','hole diameters','lens and component envelope','connector and ribbon clearance']}}
(O/'sensor_interfaces.json').write_text(json.dumps(r,ensure_ascii=False,indent=2));print(json.dumps(r,ensure_ascii=False,indent=2))
