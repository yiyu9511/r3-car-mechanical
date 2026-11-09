import sys,os,json
from pathlib import Path
sys.path.insert(0,os.environ['PATH_TO_FREECAD_LIBDIR']);import FreeCAD as A,Part
R=Path(__file__).resolve().parents[2];O=R/'cad_solidcraft/build/sensors';O.mkdir(parents=True,exist_ok=True)
s=Part.read(str(R/'models/单线雷达总装.STEP'))
D=A.newDocument('LidarAudit')
for name,indices in [('LidarHousing',[19]),('LidarScanner',[20,21]),('LidarMountEars',[13,14]),('LidarOriginalFasteners',[0,1,2,3,11,12,15,16]),('LidarConnector',[4,10,17,18])]:
 obj=D.addObject('Part::Feature',name);obj.Label=name;obj.Shape=Part.makeCompound([s.Solids[i] for i in indices])
Part.export(D.Objects,str(O/'lidar_inspection.step'))
A.closeDocument(D.Name)
print('Inspection reference exported; source geometry unchanged')
