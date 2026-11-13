"""OCCT fallback for SolidCraft's failed mixed conical/quarter-cut booleans.
Inputs are current frame and rod datums; output remains a review, not physical acceptance.
"""
import json, math
from cad_common import Part, ROOT, V
B=ROOT/'cad_solidcraft'
frame=Part.read(str(B/'review/lidar_frame_open.step'))
frame=frame.cut(Part.makeBox(100,100,10,V(-50,-50,33)))
frame=frame.cut(Part.makeBox(100,100,29.1,V(-50,-50,-.1)))
anchors=[h['xy'] for h in json.loads((B/'checks/lidar_anchor_selection.json').read_text())['proposed_anchors']]
for x,wy in anchors:
    y=wy-55
    growth=Part.makeCone(7,4,3,V(x,y,3))
    growth=growth.fuse(Part.makeCylinder(7,3.1,V(x,y,0)))
    growth=growth.fuse(Part.makeBox(8,8,26.5,V(x-4,y-4,2.8)))
    frame=frame.fuse(growth)
    frame=frame.cut(Part.makeCylinder(1.25,9.1,V(x,y,-.1)))
    if wy>60:
        nx=-26 if x<0 else 26;ny=81.613399283666-55
        frame=frame.cut(Part.makeCylinder(3,4.3,V(nx,ny,-.1)))
        frame=frame.cut(Part.makeCylinder(1.8,25.3,V(nx,ny,4.1)))
rods=[]
for side in [-1,1]:
    a,b=sorted([p for p in anchors if p[0]*side>0],key=lambda p:p[1])
    length=math.hypot(b[0]-a[0],b[1]-a[1]);u=[(b[0]-a[0])/length,(b[1]-a[1])/length,0]
    for z in [13,21]:
        def point(t):return [a[0]+u[0]*t,a[1]-55+u[1]*t,z]
        rods.append({'name':f'CableRod_{"L" if side<0 else "R"}_{z}',
                     'base':point(-5),'axis':u,'length':length+12,
                     'head_base':point(-6.5),'tip_pin_center':point(length+5),'z':z})
spec={'heights_mm':[13,21],'hole_diameter_mm':3.4,'rod_diameter_mm':3,'rods':rods}
# Regenerate these derived datums; rebuilding must not require a committed check report.
(B/'checks/lidar_cable_rods_spec.json').write_text(json.dumps(spec,indent=2)+'\n')
for s in spec['rods']:
    u=V(*s['axis']);p=V(*s['base'])-u*2
    frame=frame.cut(Part.makeCylinder(1.7,s['length']+4,p,u))
for i,x in enumerate([-25.5,25.5],1):
    frame=frame.cut(Part.makeCylinder(2.7,1.7,V(x,8.3,31.4)))
    sleeve=Part.makeCylinder(4.2,2.5,V(x,8.3,33)).fuse(Part.makeCylinder(2.5,1.6,V(x,8.3,31.5)))
    sleeve=sleeve.cut(Part.makeCylinder(1.65,4.2,V(x,8.3,31.4))).removeSplitter()
    assert sleeve.isValid() and len(sleeve.Solids)==1
    sleeve.exportStep(str(B/f'review/LocatorSleeve{i}.step'))
# Keep Boolean seams: OCCT removeSplitter makes this circular relief invalid.
assert frame.isValid() and frame.isClosed() and len(frame.Solids)==1
frame.exportStep(str(B/'review/lidar_frame_cable.step'))
print('Prepared flat frame, closed screw seats, neighbor circular relief and sleeves',flush=True)
