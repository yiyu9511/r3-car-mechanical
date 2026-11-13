"""Check rod concept STEP geometry and protected mounting regions."""
import json, math
from cad_common import Part, ROOT, V
import Mesh, MeshPart
B=ROOT/'cad_solidcraft'
spec=json.loads((B/'checks/lidar_cable_rods_spec.json').read_text())
frame=Part.read(str(B/'review/lidar_frame_cable.step'))
source=Part.read(str(B/'review/lidar_frame_open.step'))
checks={'frame_single_valid_closed':len(frame.Solids)==1 and frame.isValid() and frame.isClosed()}
details={}
steel=Part.read(str(B/'exports/steel_plate.step'))
steel_top=steel.optimalBoundingBox().ZMax
anchors=[h['xy'] for h in json.loads((B/'checks/lidar_anchor_selection.json').read_text())['proposed_anchors']]
comparison=source.copy()
for x,wy in anchors:
    if wy<60:continue
    y=wy-55
    nx=-26 if x<0 else 26;ny=81.613399283666-55
    head=Part.makeCylinder(3,4.3,V(nx,ny,-.1))
    shank=Part.makeCylinder(1.8,25.3,V(nx,ny,4.1))
    comparison=comparison.cut(head).cut(shank)
    checks[f'front_{x}_neighbor_head_clear']=frame.common(head).Volume<.001
    checks[f'front_{x}_neighbor_shank_clear']=frame.common(shank).Volume<.001
    wall=math.hypot(x-nx,y-ny)-3-1.25
    details[f'front_{x}_minimum_screw_wall_mm']=wall
    ring=Part.makeCylinder(1.25+wall-.001,8.999,V(x,y,.001)).cut(Part.makeCylinder(1.251,9.1,V(x,y,0)))
    checks[f'front_{x}_screw_wall_full_360']=ring.cut(frame).Volume<.001
    post_section=Part.makeBox(7.998,7.998,1,V(x-3.999,y-3.999,9.5)).cut(shank)
    checks[f'front_{x}_upper_post_except_shank_relief']=post_section.cut(frame).Volume<.001
for label,z,height in [('upper_plate_above_old_relief',29.41,1.98)]:
    region=Part.makeBox(100,100,height,V(-50,-50,z))
    a,b=comparison.common(region),frame.common(region)
    diff=a.cut(b).Volume+b.cut(a).Volume
    details[label+'_difference_mm3']=diff;checks[label+'_unchanged']=diff<.001
for i,(x,wy) in enumerate(anchors):
    y=wy-55
    foot=frame.common(Part.makeBox(16,16,.1,V(x-8,y-8,0)))
    expected=Part.makeCylinder(7,.1,V(x,y,0)).cut(Part.makeCylinder(1.25,.1,V(x,y,0)))
    if wy>60:
        nx=-26 if x<0 else 26;ny=81.613399283666-55
        expected=expected.cut(Part.makeCylinder(3,.3,V(nx,ny,-.1)))
    diff=foot.cut(expected).Volume+expected.cut(foot).Volume
    checks[f'foot_{i}_contact_shape']=diff<.001
    section=frame.common(Part.makeBox(16,16,.5,V(x-8,y-8,9.5)))
    square_section=Part.makeBox(8,8,.5,V(x-4,y-4,9.5))
    shank=Part.makeCylinder(1.8,25.3,V(-26 if x<0 else 26,81.613399283666-55,4.1))
    if wy>60:square_section=square_section.cut(shank)
    checks[f'post_{i}_square_section']=section.cut(square_section).Volume+square_section.cut(section).Volume<.001
    top_section=frame.common(Part.makeBox(16,16,.5,V(x-8,y-8,28)))
    top_square=Part.makeBox(8,8,.5,V(x-4,y-4,28))
    if wy>60:top_square=top_square.cut(shank)
    checks[f'post_{i}_no_top_transition']=top_section.cut(top_square).Volume+top_square.cut(top_section).Volume<.001
    if wy>60:
        nx=-26 if x<0 else 26;ny=81.613399283666-55
        details[f'front_{i}_legacy_D6_head_probe_overlap_mm3']=frame.common(Part.makeCylinder(3,4.2,V(nx,ny,0))).Volume
checks['flat_top_z33']=abs(frame.optimalBoundingBox().ZMax-33)<.001
anchors=[h['xy'] for h in json.loads((B/'checks/lidar_anchor_selection.json').read_text())['proposed_anchors']]
for i,(x,wy) in enumerate(anchors):
    y=wy-55
    checks[f'pilot_{i}_clear']=frame.common(Part.makeCylinder(1.249,9,V(x,y,0))).Volume<.001
    # Probe both sides of the circular taper's 45-degree boundary, away from the relief.
    for z in [3.2,3.6,4.0]:
        half=10-z;sign=-1 if x>0 else 1
        checks[f'foot_taper_inside_{i}_{z}']=frame.isInside(V(x+sign*(half-.03),y,z),1e-6,True)
        checks[f'foot_taper_outside_{i}_{z}']=not frame.isInside(V(x+sign*(half+.03),y,z),1e-6,True)
sleeves=[]
for i in [1,2]:
    sleeve=Part.read(str(B/f'review/LocatorSleeve{i}.step'));sleeves.append(sleeve)
    checks[f'sleeve_{i}_valid']=sleeve.isValid() and sleeve.isClosed() and len(sleeve.Solids)==1
    checks[f'sleeve_{i}_no_overlap']=frame.common(sleeve).Volume<.001
    checks[f'sleeve_{i}_seated']=sleeve.distToShape(frame)[0]<.001
    checks[f'sleeve_{i}_height']=abs(sleeve.optimalBoundingBox().ZMax-35.5)<.001
old=source.common(Part.makeBox(100,100,3,V(-50,-50,33)))
new=Part.makeCompound(sleeves).common(Part.makeBox(100,100,3,V(-50,-50,33)))
diff=old.cut(new).Volume+new.cut(old).Volume
details['external_locator_interface_difference_mm3']=diff;checks['locator_interface_preserved']=diff<.001
for name,shape,top in [('lidar_frame_flat',frame,33),('lidar_locator_sleeve',sleeves[0],35.5)]:
    shape=shape.copy();shape.rotate(V(),V(1,0,0),180);shape.translate(V(0,0,top))
    if name=='lidar_locator_sleeve':shape.translate(V(25.5,8.3,0))
    shape.exportStep(str(B/f'review/{name}_print.step'))
    mesh=MeshPart.meshFromShape(Shape=shape,LinearDeflection=.03,AngularDeflection=.15)
    path=B/f'exports/{name}.stl';mesh.write(str(path));read=Mesh.Mesh(str(path))
    checks[name+'_STL_closed']=read.isSolid()
    checks[name+'_STL_volume']=abs(abs(read.Volume)-shape.Volume)/shape.Volume<.001
    read_step=Part.read(str(B/f'review/{name}_print.step'))
    checks[name+'_bed_z0']=abs(read_step.optimalBoundingBox().ZMin)<.001 and abs(read.BoundBox.ZMin)<.001
for s in spec['rods']:
    rod=Part.read(str(B/f'review/{s["name"]}.step'))
    checks[s['name']+'_valid']=len(rod.Solids)==1 and rod.isValid() and rod.isClosed()
    overlap=frame.common(rod).Volume;gap=frame.distToShape(rod)[0]
    details[s['name']]={'frame_intersection_mm3':overlap,'minimum_gap_mm':gap}
    checks[s['name']+'_clearance']=overlap<.001 and gap>.19
    u=V(*s['axis']);p=V(*s['base'])-u*2
    bore=Part.makeCylinder(1.699,s['length']+4,p,u)
    checks[s['name']+'_through_bores']=frame.common(bore).Volume<.001
report={'checks':checks,'details':details,'pilot_to_lower_hole_material_mm':13-1.7-9,
        'between_holes_material_mm':21-13-3.4,'upper_hole_to_plate_mm':29-21-1.7,
        'limitations':['No slicing, printed fit or strength validation; round horizontal holes may still need local support','Closed front screw seats restored; actual self-tapping retention unverified','Nominal D6 head relief restored with zero added clearance; actual screw fit unverified','Not a load-bearing brace','Optional retention wire not modeled','Assembly insertion with actual camera and cables not verified'],
        'front_foot_relief':{'type':'original neighbor circular relief','head_radius_mm':3,'head_top_mm':4.2,'shank_radius_mm':1.8,'foot_diameter_mm':14,'pilot_diameter_mm':2.5,'upper_posts':'square 8x8 directly meets plate; no top transition'},
        'print_orientation':'Main top face on bed; sleeve flange on bed, print two identical sleeves; rods separate',
        'sleeve_dimensions_mm':{'flange_OD':8.4,'flange_height':2.5,'spigot_OD':5,'spigot_depth':1.5,'socket_OD':5.4,'socket_depth':1.6,'bore':3.3}}
(B/'checks/lidar_cable_rods.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2),flush=True)
assert all(checks.values())
