from pathlib import Path
import os,sys,json,math
from sc_mcp import Client
R=Path(__file__).resolve().parents[2];O=R/'cad_solidcraft/build/cat'
with Client(R,timeout=300) as c:
 print('BEFORE',c.call('inspect_design')['name'],flush=True)
 c.execute('file.new',name='CAT mount — four straight ribs / recessed nuts')
 # Native plate and copied exact source slot/hole boundaries.
 audit=json.loads((O/'source_audit.json').read_text())
 for n,v in {'plate_thickness':5,'post_height':10,'post_radius':4,'foot_radius':6,'foot_height':1.2,'pilot_radius':1.25,'pilot_depth':9,'rib_reach':5.8,'rib_thickness':2}.items():c.call('set_parameter',{'name':n,'value':v,'unit':'mm'})
 target=['CATMount']
 c.execute('solid.box',name='CAT measured bottom outline',body_name='CATMount',corner=[-67.66300877886484,-49,'-plate_thickness'],length=135.32557355773027,width=98,height='plate_thickness')
 def cylinder(label,base,r,h,op):return c.execute('solid.cylinder',name=label,base=base,radius=r,height=h,operation=op,targets=target)
 for i,w in enumerate(audit['wires']):
  x0,x1,y0,y1,_,_=w['bbox'];dx=x1-x0;dy=y1-y0
  if dx>100:continue
  if dx<4:
   cylinder(f'Shell mounting hole {i+1}',[(x0+x1)/2,(y0+y1)/2,-5.1],dx/2,5.2,'cut')
  else:
   print('Vent',i,flush=True)
   # Two semicircles and the rectangle exactly match the imported round-ended slot.
   radius=dy/2;yc=(y0+y1)/2
   c.execute('solid.box',name=f'Vent slot core {i}',corner=[x0+radius,y0,-5.1],length=dx-2*radius,width=dy,height=5.2,operation='cut',targets=target)
   for x in [x0+radius,x1-radius]:cylinder(f'Vent slot end {i}',[x,yc,-5.1],radius,5.2,'cut')
 # Six pockets recessed into the uniform plate; bottom -5, pocket roof -2.4.
 for col,x in enumerate([-25.8630087788648,29.1369912211352],1):
  for row,y in enumerate([-7.5,0,7.5],1):
   print('Recessed nut',col,row,flush=True)
   c.execute('sketch.create',plane='XY',offset=-5.1,name=f'M3 nut pocket {col}.{row}')
   c.execute('sketch.polygon.inscribed',center=[x,y],radius=5.8/math.sqrt(3),sides=6,angle=0)
   c.execute('sketch.finish')
   c.execute('solid.extrude',name=f'Internal M3 nut seat {col}.{row}',distance=2.7,operation='cut',targets=target)
 c.execute('view.apply',camera={'target':[0,0,-5],'yaw':-.7,'pitch':-.7,'distance':190,'fov':0})
 anchors=[h['world_xy'] for h in json.loads((O/'hole_selection_checks.json').read_text())['holes']]
 # These four source-steel anchors were confirmed by the user.
 for i,(x,wy) in enumerate(anchors,1):
  y=wy+50
  print('Post',i,flush=True)
  cylinder(f'Compact support post {i}',[x,y,'-plate_thickness - post_height'],'post_radius','post_height + 0.15','join')
  cylinder(f'Contact foot {i}',[x,y,'-plate_thickness - post_height'],'foot_radius','foot_height','join')
  # Two perpendicular bars form four full-height radial webs at 90 degrees.
  # 5.8 mm reach and 1mm half-width keep every corner inside the 6mm foot radius.
  for axis in ['X','Y']:
   print('Four-way straight web',i,axis,flush=True)
   if axis=='X':
    corner=[f'{x} - rib_reach',f'{y} - rib_thickness / 2','-plate_thickness - post_height']
    length,width='2 * rib_reach','rib_thickness'
   else:
    corner=[f'{x} - rib_thickness / 2',f'{y} - rib_reach','-plate_thickness - post_height']
    length,width='rib_thickness','2 * rib_reach'
   c.execute('solid.box',name=f'Full-height straight webs {i} {axis}',corner=corner,length=length,width=width,height='post_height + 0.15',operation='join',targets=target)
  c.call('save',{'path':str(O/'cat_mount.sc')})
 for i,(x,wy) in enumerate(anchors,1):cylinder(f'Self tapping pilot {i}',[x,wy+50,-15.1],'pilot_radius','pilot_depth + 0.1','cut')
 c.execute('browser.visibility',folder='sketches',visible=False);c.execute('browser.visibility',folder='origin',visible=False)
 c.execute('appearance.assign',bodies=target,color='#3b93b0')
 d=c.call('inspect_design');assert len(d['bodies'])==1;assert not [f for f in d['timeline'] if f.get('error')]
 c.call('save',{'path':str(O/'cat_mount.sc')});c.call('export',{'path':str(O/'cat_mount.step'),'bodies':target})
 (O/'inspect.json').write_text(json.dumps(d,ensure_ascii=False,indent=2));(O/'anchors.json').write_text(json.dumps(anchors))
 print('MEASURE',c.call('measure'),flush=True)
 c.call('screenshot',{'path':str(O/'underside.png'),'camera':{'target':[0,0,-5],'yaw':-.6,'pitch':-.65,'distance':190,'fov':0},'source':'model','width':1400,'height':1000,'grid':False,'axes':False})
 # Place onto actual second steel plate at world top Z53, raising the CAT shell by 2mm for the thicker tray.
 c.execute('solid.move',bodies=target,translate=[0,-50,68])
 a=c.execute('file.insert_step',path=str(R/'cad_solidcraft/exports/steel_plate.step'),name='Upper steel plate',matrix=[1,0,0,0,0,1,0,0,0,0,1,51.5]);print('PLATE',a,flush=True)
 b=c.execute('file.insert_step',path=str(O/'cat_shells.step'),name='CAT original shell',matrix=[1,0,0,0,0,1,0,-50,0,0,1,68]);print('SHELL',b,flush=True)
 c.execute('appearance.assign',bodies=a['bodies'],color='#a8b1b8')
 c.execute('appearance.assign',bodies=b['bodies'],color='#4c535d',opacity=.3)
 c.execute('view.apply',camera={'target':[0,-48,65],'yaw':-.65,'pitch':.3,'distance':245,'fov':0})
 c.call('save',{'path':str(O/'cat_on_plate.sc')})
 c.call('screenshot',{'path':str(O/'assembled.png'),'source':'model','camera':{'target':[0,-48,65],'yaw':-.65,'pitch':.3,'distance':245,'fov':0},'width':1400,'height':1000,'grid':False,'axes':False})
 c.execute('browser.visibility',items=b['bodies'],visible=False)
 c.execute('view.apply',camera={'target':[0,-48,55],'yaw':-.65,'pitch':.35,'distance':235,'fov':0})
 c.call('screenshot',{'path':str(O/'mount_on_plate.png'),'source':'model','width':1400,'height':1000,'grid':False,'axes':False})
 c.execute('browser.visibility',items=a['bodies']+b['bodies'],visible=False)
 c.execute('view.apply',camera={'target':[0,-50,61],'yaw':-.6,'pitch':-.65,'distance':195,'fov':0})
 print('DONE',flush=True)
