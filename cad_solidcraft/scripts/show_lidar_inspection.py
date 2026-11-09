import sys,json
from pathlib import Path
from sc_mcp import Client
R=Path(__file__).resolve().parents[2];O=R/'cad_solidcraft/build/sensors'
with Client(R,timeout=300) as c:
 c.call('open',{'path':str(O/'lidar_inspection.step')})
 d=c.call('inspect_design');print('BODIES',[b['name'] for b in d['bodies']],flush=True)
 for b in d['bodies']:
  n=b['name'];col='#8da4b8' if 'Housing' in n else '#444b55'
  if 'Ears' in n:col='#dbaf59'
  c.execute('appearance.assign',bodies=[n],color=col)
 # Wire rings sit outside the source surfaces; these are labels, not actual new hardware.
 targets=[('B1',[-8.3,-25.5,-30.42],[0,0,1],1.25,'#e34c4c'),('B2',[-8.3,25.5,-30.42],[0,0,1],1.25,'#e34c4c'),('S1',[30.52,-34.4,-13.5],[1,0,0],2.15,'#29a67c'),('S2',[30.52,34.4,-13.5],[1,0,0],2.15,'#29a67c')]
 for id,point,axis,rad,col in targets:
  # Bottom rings start slightly below recessed seating plane.
  if id.startswith('B'):point[2]-=.12
  c.execute('solid.cylinder',name=id+' annotation',body_name=id+'_marker',base=point,axis=axis,radius=rad+.45,height=.1,operation='new')
  p=[point[k]-.01*axis[k] for k in range(3)]
  c.execute('solid.cylinder',base=p,axis=axis,radius=rad+.08,height=.13,operation='cut',targets=[id+'_marker'])
  c.execute('appearance.assign',bodies=[id+'_marker'],color=col)
  if id.startswith('B'):
   c.execute('sketch.create',plane={'origin':[0,0,-33.05],'x_dir':[1,0,0],'y_dir':[0,-1,0]},name=id+' label')
   at=[-6,-point[1]]
  else:
   c.execute('sketch.create',plane={'origin':[30.7,0,0],'x_dir':[0,1,0],'y_dir':[0,0,1]},name=id+' label')
   at=[point[1]-3,-7]
  c.execute('sketch.text',text=id,at=at,height=3)
  c.execute('sketch.finish');t=c.execute('solid.extrude',distance=.08,operation='new',body_name=id+'_label')
  c.execute('appearance.assign',bodies=t['created_bodies'],color=col)
 c.execute('browser.visibility',folder='origin',visible=False);c.execute('browser.visibility',folder='sketches',visible=False)
 bottom={'target':[0,0,-20],'yaw':0,'pitch':-1.57079632679,'distance':125,'fov':0}
 side={'target':[0,0,6],'yaw':-1.57079632679,'pitch':.08,'distance':180,'fov':0}
 iso={'target':[0,0,6],'yaw':-1.0,'pitch':-.45,'distance':180,'fov':0}
 for name,cam in [('Bottom holes B1 B2',bottom),('Side ear holes S1 S2',side),('Mount interfaces ISO',iso)]:c.execute('view.save',name=name,camera=cam)
 c.execute('view.apply',camera=bottom)
 c.call('save',{'path':str(R/'cad_solidcraft/lidar_mount_inspection.sc')})
 for name,cam in [('lidar_bottom',bottom),('lidar_side',side),('lidar_interfaces',iso)]:
  c.call('screenshot',{'path':str(O/(name+'.png')),'camera':cam,'width':1400,'height':1000,'source':'model','grid':False,'axes':False})
 c.execute('view.apply',camera=bottom)
 # Window capture is optional when the window is obscured; model images are saved above.
 print('GUI BOTTOM INSPECTION READY',flush=True)
