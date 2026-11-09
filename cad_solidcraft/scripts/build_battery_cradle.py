"""Reference-based SolidCraft cradle, M3 10+4 male/female brass standoffs.
No geometry or script from previous cradle revisions is used.
"""
from pathlib import Path
import os,json,math
from sc_mcp import Client
ROOT=Path(__file__).resolve().parents[2]
OUT=Path(os.environ.get('R3_CAD_OUT',str(ROOT/'cad_solidcraft/build')));OUT.mkdir(parents=True,exist_ok=True)
anchors=[(-25.57,-39.04),(-25.57,39.04),(25.57,-43),(25.57,43)]
with Client(ROOT) as c:
 c.call('open',{'path':str(ROOT/'models/电池托架参考.step')})
 ref=min(c.call('inspect_design')['bodies'],key=lambda b:b['volume_mm3'])
 assert abs(ref['bbox']['max'][0]-ref['bbox']['min'][0]-66.6)<.001
 c.execute('file.new',name='Battery cradle — M3 10+4 brass standoffs')
 name='BatteryCradle';target=[name]
 params={'strap_width':6,'strap_offset':11,'strap_depth':1.2,'floor_thickness':2,'seat_drop':2.4,'seat_radius':5.5,'stud_clearance_radius':1.65,'nut_pocket_af':5.8,'nut_seat_z':-1,'brass_height':10,'stud_length':4}
 for k,v in params.items():c.call('set_parameter',{'name':k,'value':v,'unit':'mm'})
 def box(label,corner,l,w,h,op='cut'):
  print(label,flush=True);return c.execute('solid.box',name=label,corner=corner,length=l,width=w,height=h,operation=op,targets=target)
 def cylinder(label,base,r,h,op='join',targets=target,body=None):
  p=dict(name=label,base=base,radius=r,height=h,operation=op,targets=targets)
  if body:p['body_name']=body
  print(label,flush=True);return c.execute('solid.cylinder',**p)
 def hexagon(label,x,y,z,af,height,op,targets,body=None):
  sk=c.execute('sketch.create',plane='XY',offset=z,name=label+' sketch')
  c.execute('sketch.polygon.inscribed',center=[x,y],radius=af/math.sqrt(3),sides=6,angle=0)
  c.execute('sketch.finish')
  p=dict(name=label,distance=height,operation=op,targets=targets)
  if body:p['body_name']=body
  return c.execute('solid.extrude',**p)
 c.execute('solid.box',name='Measured reference envelope',body_name=name,corner=[-33.3,-45.3,'-seat_drop'],length=66.6,width=90.6,height='12 + seat_drop')
 box('Measured reference battery cavity',[-31.3,-43.3,'floor_thickness'],62.6,86.6,13)
 box('Measured reference cable opening',[-34,-41,'floor_thickness'],3,16,13)
 c.execute('view.apply',view='iso')
 # Two integrated edge rails cover all four mounts. External corners taper by 2 mm.
 for side in [-1,1]:
  print('Integrated functional edge',side,flush=True)
  c.execute('sketch.create',plane='XY',offset='-seat_drop',name=f'Functional edge {side} outline')
  pts=[[-33.3,side*33.5],[33.3,side*33.5],[33.3,side*47],[31.3,side*49],[-31.3,side*49],[-33.3,side*47]]
  c.execute('sketch.line',points=pts+[pts[0]])
  c.execute('sketch.finish')
  c.execute('solid.extrude',name=f'Integrated functional edge {side}',distance='seat_drop + floor_thickness',operation='join',targets=target)
  c.call('save',{'path':str(OUT/'battery_cradle.sc')})
 for i,(x,y) in enumerate(anchors,1):
  print('Nut trap',i,flush=True)
  hexagon(f'M3 nut access and trap {i}',x,y,-1,5.8,14,'cut',target)
  cylinder(f'M3 stud clearance {i}',[x,y,-2.5],'stud_clearance_radius',15,'cut')
 for sign in [-1,1]:
  start=f'{sign} * strap_offset - strap_width / 2'
  box('Uninterrupted central strap underside',[start,-60,-4],'strap_width',120,'4 - seat_drop + strap_depth')
  for y in [-50,43.3]:box('Strap end-wall and rail opening',[start,y,'-seat_drop + strap_depth'],'strap_width',6.7,20)
 c.execute('appearance.assign',bodies=target,color='#e89d32')
 c.execute('browser.visibility',folder='sketches',visible=False)
 c.execute('browser.visibility',folder='origin',visible=False)
 data=c.call('inspect_design');assert len(data['bodies'])==1
 assert not [f for f in data['timeline'] if f.get('error')]
 c.call('save',{'path':str(OUT/'battery_cradle.sc')})
 c.call('export',{'path':str(OUT/'battery_cradle.step'),'bodies':target})
 (OUT/'solidcraft_inspect.json').write_text(json.dumps(data,ensure_ascii=False,indent=2))
 print('PRINTABLE',c.call('measure'),flush=True)
 for view in ['iso','bottom','top']:
  c.call('screenshot',{'path':str(OUT/(view+'.png')),'view':view,'source':'model','width':1400,'height':1100,'grid':False,'axes':False})
 # Hardware is illustrative, separate bodies, never part of the printable export.
 hardware=[]
 for i,(x,y) in enumerate(anchors,1):
  brass=f'Brass_M3_10plus4_{i}';nut=f'M3_nut_{i}'
  print('Hardware',i,flush=True)
  hexagon('10 mm brass hex body '+str(i),x,y,-12.4,5.5,10,'new',[],brass)
  cylinder('4 mm male stud '+str(i),[x,y,-2.5],1.5,4.1,'join',[brass])
  # Female M3 bore is a nominal envelope, depth intentionally left unclaimed.
  cylinder('M3 female bore envelope '+str(i),[x,y,-12.5],1.5,6.1,'cut',[brass])
  hexagon('M3 nut '+str(i),x,y,-1,5.5,2.4,'new',[],nut)
  cylinder('M3 nut thread envelope '+str(i),[x,y,-1.1],1.5,2.6,'cut',[nut])
  c.execute('appearance.assign',bodies=[brass],color='#b79547')
  c.execute('appearance.assign',bodies=[nut],color='#a9b2bb')
  hardware.extend([brass,nut])
 c.execute('browser.visibility',folder='sketches',visible=False)
 c.execute('browser.visibility',folder='origin',visible=False)
 c.execute('view.apply',view='iso')
 c.call('save',{'path':str(OUT/'battery_mount.sc')})
 c.call('export',{'path':str(OUT/'battery_mount.step')})
 c.call('screenshot',{'path':str(OUT/'with_brass.png'),'view':'iso','source':'model','width':1400,'height':1100,'grid':False,'axes':False})
 print('DONE',OUT,flush=True)
