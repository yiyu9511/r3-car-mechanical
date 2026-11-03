"""Rebuild the current R3 + C30D reference from STEP, with 6 mm standoffs."""
import hashlib
import json
import math
from cad_common import App, Part, ROOT, V, bounds, horizontal_faces

OUT = ROOT/'output/current'
OUT.mkdir(parents=True, exist_ok=True)
(ROOT/'assemblies').mkdir(exist_ok=True)
sources = {'chassis':ROOT/'models/R3mini四驱小车底盘（无悬挂）_utf8.stp',
           'C30D':ROOT/'models/C30D-V2.2_2026.04.20.stp'}
chassis = Part.read(str(sources['chassis']))
board = Part.read(str(sources['C30D']))
plate = max([s for s in chassis.Solids if s.BoundBox.ZLength < 2], key=lambda s: s.Volume)
top_z = plate.BoundBox.ZMax
pcb_faces = sorted(horizontal_faces(board, 4000), key=lambda f:f.CenterOfMass.z)
pcb_bottom, pcb_top = pcb_faces[0].CenterOfMass.z, pcb_faces[-1].CenterOfMass.z
board_holes = {}
for f in board.Faces:
    c=f.Surface
    if (isinstance(c,Part.Cylinder) and abs(c.Axis.z)>.999 and 1.50<c.Radius<1.52
        and abs(f.BoundBox.ZMin-pcb_bottom)<.001 and abs(f.BoundBox.ZMax-pcb_top)<.001):
        board_holes[(round(c.Center.y,4),round(c.Center.x,4))] = (c.Center.x,c.Center.y)
board_holes = [board_holes[k] for k in sorted(board_holes)]
assert len(board_holes)==4
plate_cylinders = [f.Surface for f in plate.Faces if isinstance(f.Surface,Part.Cylinder)
                   and abs(f.Surface.Axis.z)>.999 and 1.2<f.Surface.Radius<1.7]
targets=[]
for x,y in [(-21.05,-29.79),(36.95,-29.79),(-21.05,19.21),(36.95,19.21)]:
    c=min(plate_cylinders,key=lambda c:math.hypot(c.Center.x-x,c.Center.y-y))
    assert math.hypot(c.Center.x-x,c.Center.y-y)<.02
    targets.append((c.Center.x,c.Center.y,2*c.Radius))
dx=sum(t[0]-h[0] for t,h in zip(targets,board_holes))/4
dy=sum(t[1]-h[1] for t,h in zip(targets,board_holes))/4
doc=App.newDocument('C30D_Current')
doc.Label='当前基线：R3 + C30D · 6 mm 铜柱'
params=doc.addObject('Spreadsheet::Sheet','Params')
for row,(name,value) in enumerate([('standoff_h',6),('base_z',top_z),('pcb_local_z',pcb_bottom)],1):
    params.set('A'+str(row),name);params.set('B'+str(row),f'={value:.10f} mm');params.setAlias('B'+str(row),name)
ch=doc.addObject('Part::Feature','Chassis_R3mini');ch.Label='R3 mini 底盘';ch.Shape=chassis
pcb=doc.addObject('Part::Feature','C30D_V2_2');pcb.Label='C30D V2.3（使用 V2.2 外形参考）';pcb.Shape=board
pcb.Placement.Base=V(dx,dy,0)
pcb.setExpression('Placement.Base.z','Params.base_z + Params.standoff_h - Params.pcb_local_z')
hardware=[]
for i,(x,y,diameter) in enumerate(targets,1):
    outer=doc.addObject('Part::Cylinder',f'SpacerOuter{i}');outer.Radius=2.5
    inner=doc.addObject('Part::Cylinder',f'SpacerBore{i}');inner.Radius=1.3
    for o in [outer,inner]:
        o.Placement.Base=V(x,y,top_z);o.setExpression('Height','Params.standoff_h')
    spacer=doc.addObject('Part::Cut',f'Spacer{i}');spacer.Label=f'M2.5×6 铜柱示意 {i}'
    spacer.Base=outer;spacer.Tool=inner;hardware.append(spacer)
doc.recompute()
assert pcb.Shape.BoundBox.ZMin>top_z
for spacer in hardware:assert spacer.Shape.isValid() and len(spacer.Shape.Solids)==1
original_min=pcb.Shape.BoundBox.ZMin
params.set('B1','=7 mm');doc.recompute()
assert abs(pcb.Shape.BoundBox.ZMin-original_min-1)<1e-5
assert all(abs(s.Shape.BoundBox.ZLength-7)<1e-5 for s in hardware)
params.set('B1','=6 mm');doc.recompute()
for o in doc.Objects:
    if hasattr(o,'Visibility'):o.Visibility=False
for o in [ch,pcb]+hardware:o.Visibility=True
path=ROOT/'assemblies/c30d_on_chassis.FCStd'
doc.saveAs(str(path))
positions=[]
for h,t in zip(board_holes,targets):
    actual=(h[0]+dx,h[1]+dy)
    positions.append({'board_xy_mm':actual,'chassis_xy_mm':t[:2],'chassis_diameter_mm':t[2],
                      'error_mm':math.hypot(actual[0]-t[0],actual[1]-t[1])})
assert max(p['error_mm'] for p in positions)<.001
report={'stage':'current C30D reference; CAT/battery layout remains provisional',
        'sources':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources.values()},
        'placement_mm':[dx,dy,pcb.Placement.Base.z],'standoff_height_mm':6,
        'chassis_top_z_mm':top_z,'pcb_bottom_z_mm':pcb_bottom+pcb.Placement.Base.z,
        'pcb_top_z_mm':pcb_top+pcb.Placement.Base.z,'board_bbox_mm':bounds(pcb.Shape),
        'lowest_component_gap_mm':pcb.Shape.BoundBox.ZMin-top_z,
        'mounts':positions,'parameter_change_check':'pass',
        'not_tested':['Physical hardware tolerances','Cable/connector/service access']}
App.closeDocument(doc.Name)
saved=App.openDocument(str(path));saved.recompute()
assert abs(saved.getObject('C30D_V2_2').Placement.Base.z-report['placement_mm'][2])<1e-6
assert not [o.Name for o in saved.Objects if any('Error' in str(s) or 'Invalid' in str(s) for s in o.State)]
report['saved_readback']='pass'
(OUT/'baseline_checks.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
print(json.dumps(report,ensure_ascii=False,indent=2),flush=True)
