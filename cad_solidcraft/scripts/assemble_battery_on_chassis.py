"""Place current native battery mount on original chassis, then snapshot without changing source files."""
from pathlib import Path
import json
from sc_mcp import Client
ROOT=Path(__file__).resolve().parents[2]
with Client(ROOT,timeout=300) as c:
 c.call('open',{'path':str(ROOT/'cad_solidcraft/battery_mount.sc')})
 names=[b['name'] for b in c.call('inspect_design')['bodies']]
 c.execute('solid.move',bodies=names,axis=[0,0,1],angle=-90)
 c.execute('solid.move',bodies=names,translate=[0,-102.9,13.9])
 c.execute('file.insert_step',path=str(ROOT/'models/R3mini四驱小车底盘（无悬挂）_utf8.stp'),name='R3 original chassis')
 cam={'target':[0,-35,0],'yaw':-.55,'pitch':.65,'distance':365,'fov':0}
 c.execute('view.apply',camera=cam)
 c.execute('browser.visibility',folder='origin',visible=False)
 c.execute('browser.visibility',folder='sketches',visible=False)
 c.call('save',{'path':str(ROOT/'cad_solidcraft/battery_on_chassis.sc')})
 c.call('screenshot',{'source':'model','path':str(ROOT/'cad_solidcraft/renders/battery_on_chassis.png'),'camera':cam,'width':1400,'height':1000,'grid':False,'axes':False})
 scene=c.execute('render.scene');mount=next(b for b in scene['bodies'] if b['name']=='BatteryCradle')
 assert abs(mount['bounds']['min'][2]-11.5)<.001
 (ROOT/'cad_solidcraft/checks/battery_on_chassis.json').write_text(json.dumps({'status':'pass','scope':'current native cradle placement on original chassis; no TOF/other equipment in this scene','world_bounds':mount['bounds'],'source':'cad_solidcraft/battery_mount.sc'},indent=2))
 print('CURRENT BATTERY ASSEMBLY SAVED',flush=True)
