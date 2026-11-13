"""Visible print orientation of the flat frame and two separate locator sleeves."""
from pathlib import Path
import json,math
from sc_mcp import Client
R=Path(__file__).resolve().parents[2];B=R/'cad_solidcraft'
with Client(R,timeout=300) as c:
    c.execute('file.new',name='LiDAR flat frame - inverted printing and separate sleeves')
    for name,file,x,color in [('FlatFrame','lidar_frame_flat_print',0,'#398ba4'),('Sleeve1','lidar_locator_sleeve_print',48,'#d9ab58'),('Sleeve2','lidar_locator_sleeve_print',60,'#d9ab58')]:
        r=c.execute('file.insert_step',path=str(B/f'review/{file}.step'),name=name,matrix=[1,0,0,x,0,1,0,-48 if x else 0,0,0,1,0])
        c.execute('appearance.assign',bodies=r['bodies'],color=color)
    rods=json.loads((B/'checks/lidar_cable_rods_spec.json').read_text())['rods']
    for i,s in enumerate(rods):
        angle=math.atan2(s['axis'][0],s['axis'][1]);co=math.cos(angle);si=math.sin(angle)
        hx,hy,hz=s['head_base']
        matrix=[co,-si,0,48+10*i-(co*hx-si*hy),si,co,0,-34-(si*hx+co*hy),0,0,1,3-hz]
        r=c.execute('file.insert_step',path=str(B/f'review/{s["name"]}.step'),name=s['name']+' separate display',matrix=matrix)
        c.execute('appearance.assign',bodies=r['bodies'],color='#ef9c36' if s['z']==13 else '#7cbb55')
    c.execute('browser.visibility',folder='origin',visible=False)
    cam={'target':[22,-3,12],'yaw':-.7,'pitch':.65,'distance':245,'fov':0}
    c.execute('view.apply',camera=cam)
    c.call('save',{'path':str(B/'lidar_print_layout.sc')})
    c.call('screenshot',{'path':str(B/'renders/lidar_print_layout.png'),'source':'model','camera':cam,'width':1500,'height':1000,'grid':False,'axes':False})
