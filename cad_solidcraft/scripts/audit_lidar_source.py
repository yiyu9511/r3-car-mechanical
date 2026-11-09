import sys,os,json,hashlib
from pathlib import Path
sys.path.insert(0,os.environ['PATH_TO_FREECAD_LIBDIR']);import FreeCAD as A,Part
R=Path(__file__).resolve().parents[2];p=R/'models/单线雷达总装.STEP';S=Part.read(str(p))
def xyz(v):return [round(float(k),6) for k in v]
def bounds(s):
 b=s.BoundBox;return [round(k,6) for k in [b.XMin,b.XMax,b.YMin,b.YMax,b.ZMin,b.ZMax]]
(R/'cad_solidcraft/build/sensors').mkdir(parents=True,exist_ok=True)
solids=[]
for i,s in enumerate(S.Solids):
 row={'solid':i,'volume':s.Volume,'bbox':bounds(s),'faces':len(s.Faces),'valid':s.isValid(),'cylinders':[]}
 for j,f in enumerate(s.Faces):
  q=f.Surface
  if isinstance(q,Part.Cylinder):
   if q.Radius>4.1:continue
   u0,u1,v0,v1=f.ParameterRange;pt=f.valueAt((u0+u1)/2,(v0+v1)/2);normal=f.normalAt((u0+u1)/2,(v0+v1)/2)
   radial=pt-q.Center-q.Axis*((pt-q.Center).dot(q.Axis))
   row['cylinders'].append({'face':j+1,'center':xyz(q.Center),'axis':xyz(q.Axis),'radius':q.Radius,'bbox':bounds(f),'angle_span_rad':u1-u0,'normal_dot_radial':normal.dot(radial),'orientation':f.Orientation})
 solids.append(row)
r={'source':str(p.relative_to(R)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'solid_count':len(S.Solids),'bbox':bounds(S),'solids':solids}
(R/'cad_solidcraft/build/sensors/lidar_source_audit.json').write_text(json.dumps(r,ensure_ascii=False,indent=2))
print('SOURCE',r['solid_count'],r['bbox'],flush=True)
for row in solids:
 print('SOLID',row['solid'],'volume',round(row['volume'],2),'bbox',row['bbox'],'faces',row['faces'],flush=True)
 for c in row['cylinders']:
  if c['normal_dot_radial']<0:print(' INNER',json.dumps(c),flush=True)
