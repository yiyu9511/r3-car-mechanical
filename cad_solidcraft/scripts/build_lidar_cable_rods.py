"""Visible two-height removable cable-rod concept; original open frame is input."""
import json, math
from pathlib import Path
from sc_mcp import Client
R=Path(__file__).resolve().parents[2]; B=R/'cad_solidcraft'
spec=json.loads((B/'checks/lidar_cable_rods_spec.json').read_text())['rods']
with Client(R,timeout=300) as c:
    if c.call('inspect_design',{'measure':False,'sketches':False}).get('dirty'):raise RuntimeError('Unsaved active design')
    c.execute('file.new',name='Flat LiDAR frame - closed screw seats and foot relief')
    frame=c.execute('file.insert_step',path=str(B/'review/lidar_frame_cable.step'),name='LidarFrame - closed screw seats and neighbor circular relief')['bodies']
    c.execute('appearance.assign',bodies=frame,color='#398ba4')
    for i in [1,2]:
        names=c.execute('file.insert_step',path=str(B/f'review/LocatorSleeve{i}.step'),name=f'LocatorSleeve{i}')['bodies']
        c.execute('appearance.assign',bodies=names,color='#d9ab58')
    c.call('set_parameter',{'name':'rod_radius','value':1.5,'unit':'mm'})
    for s in spec:
        c.execute('solid.cylinder',name=s['name']+' removable shaft',body_name=s['name'],base=s['base'],axis=s['axis'],radius='rod_radius',height=s['length'],operation='new')
        c.execute('solid.cylinder',name=s['name']+' stop head',base=s['head_base'],axis=s['axis'],radius=3,height=1.6,operation='join',targets=[s['name']])
        p=s['tip_pin_center'];c.execute('solid.cylinder',name=s['name']+' optional 1mm wire pin eye',base=[p[0],p[1],p[2]-2],axis='Z',radius=.6,height=4,operation='cut',targets=[s['name']])
        c.execute('appearance.assign',bodies=[s['name']],color='#ef9c36' if s['z']==13 else '#7cbb55')
        c.call('export',{'path':str(B/f'review/{s["name"]}.step'),'bodies':[s['name']]})
    cam={'target':[0,1,17],'yaw':-.85,'pitch':.23,'distance':157,'fov':0}
    c.execute('browser.visibility',folder='origin',visible=False)
    c.execute('view.apply',camera=cam)
    state=c.call('inspect_design',{'measure':False,'sketches':False})
    assert len(state['bodies'])==7 and not any(f.get('error') for f in state['timeline'])
    c.call('save',{'path':str(B/'lidar_cable_rods.sc')})
    c.call('screenshot',{'path':str(B/'renders/lidar_cable_rods.png'),'source':'model','camera':cam,'width':1500,'height':1000,'grid':False,'axes':False})
    (B/'checks/lidar_cable_rods_spec.json').write_text(json.dumps({'heights_mm':[13,21],'hole_diameter_mm':3.4,'rod_diameter_mm':3,'rods':spec,'native_errors':[],'frame_provenance':'tools/prepare_lidar_print_geometry.py; OCCT fallback for native Boolean failures','status':'visual fitting concept; retention wire not modeled; printing fit unverified'},indent=2)+'\n')
    print('Saved lidar_cable_rods.sc: flat frame, two sleeves, four rods',flush=True)
