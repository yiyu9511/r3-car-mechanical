"""Targeted native edge rounds; protect cavity datums and all fastener seats."""
def apply_battery_rounds(client, body='BatteryCradle'):
    def topology():
        return client.call('body_topology', {'body': body})['edges']
    def fillet(label, points, radius):
        if not points:
            raise RuntimeError(f'No edges found for {label}')
        print(f'{label}: {len(points)} edges, R{radius}', flush=True)
        client.execute('solid.fillet', body=body, edges=points, radius=radius)
    fillet('Outside upright corners', [e['mid'] for e in topology()
           if abs(abs(e['mid'][0])-33.3)<.001 and abs(abs(e['mid'][1])-45.3)<.001
           and abs(e['length']-10)<.001], 1.2)
    fillet('Upper wall rim', [e['mid'] for e in topology()
           if abs(e['start'][2]-12)<.001 and abs(e['end'][2]-12)<.001], .5)
    for x in [-23,-3.5,3.5,23]:
        fillet(f'Vent upper lip {x}', [e['mid'] for e in topology()
               if abs(e['start'][2]-2)<.001 and abs(e['end'][2]-2)<.001
               and abs(e['mid'][1])<28 and abs(e['mid'][0]-x)<2.01], .35)
    # SolidCraft's edge fillet does not support these end-face arrangements.
    # Subtract square-minus-quarter-cylinder tools for the exact R0.5 section.
    for x in [-14,8]:
        for sign in [-1,1]:
            tool=f'StrapEntryRound_{x}_{sign}'
            yc=sign*42.8
            ymin=42.8 if sign>0 else -43.3
            client.execute('solid.box', body_name=tool, corner=[x,ymin,1.5],
                           length=6,width=.5,height=.5,operation='new')
            client.execute('solid.cylinder',name='Strap entry R0.5 cutter',
                           base=[x-.1,yc,1.5],axis='X',radius=.5,height=6.2,
                           operation='cut',targets=[tool])
            client.execute('solid.combine',target=body,tools=[tool],operation='cut',keep_tools=False)
    # The six long exposed edges round reliably; short diagonal/wall-root junctions stay unchanged.
    fillet('Functional edge outer long lips', [e['mid'] for e in topology()
           if abs(e['start'][2]-2)<.001 and abs(e['end'][2]-2)<.001
           and abs(abs(e['mid'][1])-49)<.001], .4)
    data=client.call('inspect_design')
    errors=[f for f in data['timeline'] if f.get('error')]
    if len(data['bodies']) != 1 or errors:
        raise RuntimeError({'body_count':len(data['bodies']),'errors':errors})
