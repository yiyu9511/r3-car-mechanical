"""Functional edge finishing; no lightening windows or slicing-setting changes."""
import math

def apply_cat_finish(client, anchors, body='CATMount'):
    def edges():
        return client.call('body_topology', {'body':body})['edges']
    def apply(label,command,points,**params):
        if not points:
            raise RuntimeError(f'No edges found: {label}')
        print(label, len(points), flush=True)
        client.execute(command,body=body,edges=points,**params)
    for i,(x,world_y) in enumerate(anchors,1):
        y=world_y+50
        pts=[e['mid'] for e in edges() if abs(e['start'][2]+5)<.001 and abs(e['end'][2]+5)<.001
             and math.hypot(e['mid'][0]-x,e['mid'][1]-y)<6.2]
        apply(f'Root round {i}', 'solid.fillet', pts, radius=.6)
    pts=[e['mid'] for e in edges() if abs(e['length']-5)<.001
         and abs(abs(e['mid'][0])-67.663)<.001 and abs(abs(e['mid'][1])-49)<.001]
    apply('Plate outside corners','solid.fillet',pts,radius=3)
    # Leave the entire CAT mating perimeter unchanged. Native chamfer follows tangent
    # rounded-corner chains, so selecting only its free ends would also alter the mating sides.
    pts=[e['mid'] for e in edges() if abs(e['start'][2]+5)<.001 and abs(e['end'][2]+5)<.001
         and (abs(e['mid'][0])>64.5 or abs(e['mid'][1])>45.8)]
    apply('Bottom plate perimeter','solid.chamfer',pts,distance=.3)
    for x in [-25.8630087788648,29.1369912211352]:
        for y in [-7.5,0,7.5]:
            pts=[e['mid'] for e in edges() if abs(e['start'][2]+5)<.001 and abs(e['end'][2]+5)<.001
                 and math.hypot(e['mid'][0]-x,e['mid'][1]-y)<3.5]
            apply('Nut-pocket lead-in','solid.chamfer',pts,distance=.25)
    for x,world_y in anchors:
        y=world_y+50
        pts=[e['mid'] for e in edges() if abs(e['start'][2]+15)<.001 and abs(e['end'][2]+15)<.001
             and abs(math.hypot(e['mid'][0]-x,e['mid'][1]-y)-1.25)<.01]
        apply('Self-tapping pilot lead-in','solid.chamfer',pts,distance=.25)
    data=client.call('inspect_design')
    if len(data['bodies'])!=1 or any(f.get('error') for f in data['timeline']):
        raise RuntimeError('Finishing did not produce a single error-free body')
