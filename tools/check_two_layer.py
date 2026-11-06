"""Check current positioned solids; use an envelope for the surface-only rear TOF."""
import json
from cad_common import App, Part, ROOT, V


def global_shape(obj):
    s=obj.Shape.copy()
    s.Placement=obj.getGlobalPlacement().multiply(obj.Placement.inverse()).multiply(s.Placement)
    return s


out=ROOT/'output/two_layer'
data=json.loads((out/'two_layer_checks.json').read_text(encoding='utf-8'))
doc=App.openDocument(str(ROOT/'assemblies/two_layer.FCStd'))
names=[n for n in data['visible_object_names'] if n not in ['BatteryHeightEnvelope','CameraLensEnvelope']]
shapes={};methods={}
for n in names:
    s=global_shape(doc.getObject(n));method='solid BRep'
    if not s.Solids:
        b=s.BoundBox;s=Part.makeBox(b.XLength,b.YLength,b.ZLength,V(b.XMin,b.YMin,b.ZMin))
        method='conservative bbox envelope (source has no solids)'
    shapes[n]=s;methods[n]=method
checks=[];violations=[]
for i,a in enumerate(names):
    for b in names[i+1:]:
        sa,sb=shapes[a],shapes[b];ba,bb=sa.BoundBox,sb.BoundBox
        overlap=[min(getattr(ba,k+'Max'),getattr(bb,k+'Max'))-max(getattr(ba,k+'Min'),getattr(bb,k+'Min')) for k in ['X','Y','Z']]
        if min(overlap)<=1e-6:
            continue
        # Narrow dense device assemblies to solids that could touch this pair.
        def candidates(shape,other_box):
            solids=[]
            for part in shape.Solids:
                box=part.BoundBox
                depths=[min(getattr(box,k+'Max'),getattr(other_box,k+'Max'))-max(getattr(box,k+'Min'),getattr(other_box,k+'Min')) for k in ['X','Y','Z']]
                if min(depths)>1e-6:solids.append(part)
            return solids
        parts_a=candidates(sa,bb);parts_b=candidates(sb,ba)
        volume=Part.makeCompound(parts_a).common(Part.makeCompound(parts_b)).Volume if parts_a and parts_b else 0.0
        item={'a':a,'b':b,'overlap_mm3':volume,'method':[methods[a],methods[b]]}
        checks.append(item)
        if volume>1e-4:violations.append(item)
report={'status':'fail' if violations else 'pass','evidence_level':'geometry',
        'scope':'Positioned visible parts; excludes unconfirmed battery/lens envelopes and unrouted cable reference',
        'pair_count':len(names)*(len(names)-1)//2,'boolean_pairs':checks,'violations':violations,
        'limitations':['Touching surfaces do not prove fastener access or retention',
                       'No actual battery body, lens, antennas or final cables included',
                       'Standoff positions and all new chassis anchors remain unconfirmed']}
with open(out/'collision_checks.json','w',encoding='utf-8') as fh:
    fh.write(json.dumps(report,ensure_ascii=False,indent=2))
print(json.dumps({'status':report['status'],'pairs':report['pair_count'],'boolean_checks':len(checks),'violations':violations},ensure_ascii=False,indent=2),flush=True)
assert not violations
