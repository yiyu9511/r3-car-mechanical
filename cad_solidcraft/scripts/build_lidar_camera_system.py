"""Current modular sensor draft: confirmed frame anchors, U perforated rim, open camera guard.
Camera envelopes and LiDAR thread engagement remain trial assumptions, not print approval.
"""
from pathlib import Path
import json,math,os
from sc_mcp import Client
R=Path(__file__).resolve().parents[2];O=R/'cad_solidcraft/build/lidar_camera';O.mkdir(parents=True,exist_ok=True)
anchors=[h['xy'] for h in json.loads((R/'cad_solidcraft/checks/lidar_anchor_selection.json').read_text())['proposed_anchors']]
with Client(R,timeout=300) as c:
 c.execute('file.new',name='LiDAR frame — confirmed anchors and perforated U rim')
 def box(label,corner,size,body,op='join'):
  p=dict(name=label,corner=corner,length=size[0],width=size[1],height=size[2],operation=op)
  p['body_name' if op=='new' else 'targets']=body if op=='new' else [body]
  return c.execute('solid.box',**p)
 def cyl(label,base,r,h,body,op='join',axis='Z'):
  p=dict(name=label,base=base,radius=r,height=h,axis=axis,operation=op)
  p['body_name' if op=='new' else 'targets']=body if op=='new' else [body]
  return c.execute('solid.cylinder',**p)
 def color(names,col,opacity=1):c.execute('appearance.assign',bodies=names,color=col,opacity=opacity)
 def hexcut(body,label,origin,xdir,ydir,af,depth):
  c.execute('sketch.create',plane={'origin':origin,'x_dir':xdir,'y_dir':ydir},name=label+' profile')
  c.execute('sketch.polygon.inscribed',center=[0,0],radius=af/math.sqrt(3),sides=6,angle=0)
  c.execute('sketch.finish');return c.execute('solid.extrude',name=label,distance=depth,operation='cut',targets=[body])
 def finish_view():
  c.execute('browser.visibility',folder='origin',visible=False);c.execute('browser.visibility',folder='sketches',visible=False)
 def savepart(name,body):
  finish_view();d=c.call('inspect_design');assert len(d['bodies'])==1 and not [f for f in d['timeline'] if f.get('error')]
  c.call('save',{'path':str(O/(name+'.sc'))});c.call('export',{'path':str(O/(name+'.step')),'bodies':[body]})
  (O/(name+'_native.json')).write_text(json.dumps(d,ensure_ascii=False,indent=2))
 print('CONFIRMED-ANCHOR FRAME',flush=True)
 frame='LidarFrame'
 box('Compact top support',[-35,-36,29],[70,75,4],frame,'new')
 box('Central cable service opening',[-17,-17,28.9],[34,34,4.2],frame,'cut')
 for x in [-25.5,25.5]:
  cyl('Rear-facing LiDAR bottom-hole recess support',[x,8.3,32.8],4.2,2.7,frame)
  cyl('LiDAR M3 clearance - thread depth to confirm',[x,8.3,28.9],1.65,6.8,frame,'cut')
 for i,(x,wy) in enumerate(anchors,1):
  y=wy-55;print('Leg',i,flush=True)
  box('Frame square upright '+str(i),[x-4,y-4,2.8],[8,8,26.5],frame)
  cyl('Stepped foot '+str(i),[x,y,0],7,3.1,frame)
  # Orthogonal short root ribs at top, rather than a whole second floor.
  box('Upper X root rib',[x-6,y-1,24.5],[12,2,4.8],frame)
  box('Upper Y root rib',[x-1,y-6,24.5],[2,12,4.8],frame)
  if i>=3:
   nx=-26 if x<0 else 26;ny=81.613399283666-55
   cyl('Neighbor head/contact relief',[nx,ny,-.1],3,4.3,frame,'cut')
   cyl('Neighbor shank clearance',[nx,ny,4.1],1.8,25.3,frame,'cut')
 # Elevated ties brace the legs while keeping holes and cables accessible below them.
 for sign in [-1,1]:box('Elevated side tie',[sign*20.4-1.6,anchors[0][1]-55,8],[3.2,anchors[2][1]-anchors[0][1],3],frame)
 color([frame],'#398ba4')
 c.execute('view.apply',camera={'target':[0,0,20],'yaw':2.5,'pitch':.45,'distance':150,'fov':0})
 # U rim: front + both sides; rear absent. One native solid after unions.
 def wall_box(tag,label,corner,size,op='cut'):
  x,y,z=corner;dx,dy,dz=size
  if tag=='LEFT':corner=[4-y-dy,x,z];size=[dy,dx,dz]
  elif tag=='RIGHT':corner=[y-4,-x-dx,z];size=[dy,dx,dz]
  return box(label,corner,size,frame,op)
 def wall_cyl(tag,label,base,r,h):
  x,y,z=base
  if tag=='LEFT':base=[4-y,x,z];axis=[-1,0,0]
  elif tag=='RIGHT':base=[y-4,-x,z];axis=[1,0,0]
  else:axis='Y'
  return cyl(label,base,r,h,frame,'cut',axis)
 # Join simple strips first, then cut only local holes. Rear is intentionally open.
 for tag in ['FRONT','LEFT','RIGHT']:
  wall_box(tag,'Integral U rim '+tag,[-35,36,14],[70,3,15.3],'join')
 for x in [-35,32]:box('Continuous U front corner',[x,35,14],[3,4,15.3],frame)
 for tag in ['FRONT','LEFT','RIGHT']:
  print('OPEN RIM HOLES',tag,flush=True)
  for k,x in enumerate([-25,-15,-5,5,15,25],1):
   wall_box(tag,'Rectangular keyed interface slot',[x-3.2,35.9,22],[6.4,3.2,5])
  for x in [-20,0,20]:wall_cyl(tag,'M3 anti-lift bolt access below slots',[x,35.9,17],1.65,3.2)
 for i,(x,wy) in enumerate(anchors,1):cyl('Final M3x10 self-tap pilot '+str(i),[x,wy-55,-.1],1.25,9.1,frame,'cut')
 savepart('lidar_frame',frame)
 c.call('screenshot',{'path':str(O/'frame_underside.png'),'source':'model','camera':{'target':[0,0,18],'yaw':2.3,'pitch':-.45,'distance':165,'fov':0},'width':1400,'height':1000,'grid':False,'axes':False})
 print('CAMERA FOOT AND DOUBLE HOOK',flush=True)
 c.execute('file.new',name='Camera double-hook dock — lower steel support')
 dock='CameraDock'
 box('Dock outside crossbar',[-10,39.3,14.5],[20,5,9.6],dock,'new')
 for x in [-5,5]:
  box('Hook through rectangular slot',[x-2.8,34.8,22.1],[5.6,5,2.2],dock)
  box('Downturned retaining hook',[x-2.8,34.8,20.1],[5.6,1,2.2],dock)
 box('Dock lower spine',[-3,40,2.3],[6,4,17],dock)
 box('Steel contact foot - no chassis bolt',[-8,42,0],[16,8,2.5],dock)
 box('Pitch fork bridge',[-22.3,43,18],[44.6,2,7],dock)
 for x in [-22.3,19.3]:
  box('Pitch fork ear',[x,44,17],[3,22,14],dock)
  cyl('M3 pitch lock bore',[x-.1,61,24],1.65,3.2,dock,'cut','X')
 cyl('M3 anti-lift locking bore',[0,39.1,17],1.65,7.2,dock,'cut','Y')
 hexcut(dock,'Front inserted captive anti-lift nut',[0,41.7,17],[1,0,0],[0,0,-1],5.8,4.5)
 color([dock],'#e68446');savepart('camera_dock',dock)
 print('CAMERA SMALL DUST COVER - TRIAL ENVELOPES',flush=True)
 c.execute('file.new',name='Camera compact enclosure — unmeasured depth/optics allowances')
 housing='CameraHousing'
 # Known board29x31; allow0.6mm per side,2mm shell walls. Rear is closed by a separate lid.
 box('Outer camera shell',[-17.1,50,5.9],[34.2,16.5,36.2],housing,'new')
 box('PCB and component cavity',[-15.5,49.9,7.5],[31,14.6,33],housing,'cut')
 cyl('Lens opening D18 provisional optical center19.5mm from board bottom',[0,64.4,28],9,2.2,housing,'cut','Y')
 # Front screws pass through dedicated spacers to the PCB corner zone; no pressure on components.
 for x in [-11.5,11.5]:
  for z in [11.5,36.5]:
   cyl('Front PCB clamping spacer',[x,56.2,z],2.6,8.5,housing,axis='Y')
   cyl('Provisional M2.5 external screw passage',[x,56.1,z],1.4,10.6,housing,'cut','Y')
 for x in [-19,13]:
  cyl('Outside pitch boss',[x,61,24],4.5,6,housing,axis='X')
 cyl('M3 side pivot passage',[-19.1,61,24],1.65,38.2,housing,'cut','X')
 for x in [-15.6,13]:hexcut(housing,'M3 pitch nut inside front-side cavity',[x,61,24],[0,1,0],[0,0,1],5.8,2.6)
 color([housing],'#df956b');savepart('camera_housing',housing)
 print('CAMERA REAR LID',flush=True)
 c.execute('file.new',name='Camera rear lid — captive nuts and ribbon exit')
 lid='CameraRearLid'
 box('Rear dust cover',[-17.1,48,5.9],[34.2,2,36.2],lid,'new')
 # Four rear standoffs touch the PCB back; M2.5 nuts stay isolated2.5mm behind PCB.
 for x in [-11.5,11.5]:
  for z in [11.5,36.5]:
   cyl('Rear PCB support',[x,49.8,z],3.8,5.2,lid,axis='Y')
   cyl('External screw clearance',[x,47.9,z],1.4,7.2,lid,'cut','Y')
   hexcut(lid,'Rear accessible M2.5 nut pocket - trial AF5.3',[x,47.9,z],[1,0,0],[0,0,-1],5.3,4.6)
 # Lower rear ribbon exit; size to be finalized after measuring the cable/connector.
 box('Ribbon exit provisional16x3',[-8,47.9,8.5],[16,2.2,3],lid,'cut')
 color([lid],'#ad6a43');savepart('camera_rear_lid',lid)
 # Build the review scene from the independently editable part files.
 c.execute('file.new',name='Compact LiDAR frame + perforated U rim + compact camera enclosure — DRAFT')
 groups={}
 for key,file,col in [('frame','lidar_frame','#398ba4'),('dock','camera_dock','#e68446'),('guard','camera_housing','#df956b'),('rear_lid','camera_rear_lid','#ad6a43')]:
  r=c.execute('file.insert_step',path=str(O/(file+'.step')),name=file);groups[key]=r['bodies'];color(r['bodies'],col)
 # Source-based camera PCB reference and guessed lens envelope remain explicitly labeled.
 pcb='CameraPCB_UNMEASURED_thickness_holes';lens='CameraLens_UNMEASURED'
 box('PCB reference 29x31',[-14.5,55,8.5],[29,1.2,31],pcb,'new')
 for x in [-11.5,11.5]:
  for z in [11.5,36.5]:cyl('Drawing centers; diameter not measured',[x,54.9,z],1.25,1.4,pcb,'cut','Y')
 cyl('Lens envelope',[0,56.2,28],6,8,lens,'new','Y');color([pcb],'#258359');color([lens],'#262e39')
 # Transform guard and camera around the same X-axis pivot into10deg down-looking pose.
 theta=math.radians(-10);cy=61;cz=24
 tilted=groups['guard']+groups['rear_lid']+[pcb,lens]
 c.execute('solid.move',bodies=tilted,axis=[1,0,0],angle=-10)
 c.execute('solid.move',bodies=tilted,translate=[0,cy-(cy*math.cos(theta)-cz*math.sin(theta)),cz-(cy*math.sin(theta)+cz*math.cos(theta))])
 groups['camera_references']=[pcb,lens]
 hardware=[]
 for side in [-1,1]:
  n=f'Pitch_M3x10_{side}';start=-22.3 if side<0 else 12.3
  cyl('M3x10 pivot screw',[start,61,24],1.45,10,n,'new','X')
  cyl('Screw head',[-24.3 if side<0 else 22.3,61,24],2.75,2,n,axis='X');color([n],'#bbc2c9');hardware.append(n)
 # M3x10 anti-lift bolt from inner frame y36 toward module nut y41.7..44.1.
 n='Dock_M3x10_lock';cyl('Anti-lift M3x10',[0,36,17],1.45,10,n,'new','Y');cyl('Lock head',[0,34,17],2.75,2,n,axis='Y');color([n],'#bbc2c9');hardware.append(n)
 groups['hardware_envelopes']=hardware
 # Explicit whole-system rigid placement in the car's world coordinates.
 local=[b['name'] for b in c.call('inspect_design')['bodies']]
 c.execute('solid.move',bodies=local,translate=[0,55,53])
 # Evidence exports retain exact world placements; not a release print package.
 for key,names in groups.items():c.call('export',{'path':str(O/(key+'_world.step')),'bodies':names})
 plate=c.execute('file.insert_step',path=str(R/'cad_solidcraft/exports/steel_plate.step'),name='Original upper steel plate',matrix=[1,0,0,0,0,1,0,0,0,0,1,51.5]);color(plate['bodies'],'#abb5be')
 lidar=c.execute('file.insert_step',path=str(R/'cad_solidcraft/build/sensors/lidar_inspection.step'),name='LakiBeam1 ears and blind sector toward rear',matrix=[0,1,0,0,-1,0,0,55,0,0,1,118.92192707366391]);color(lidar['bodies'],'#657486',.4)
 cat=c.execute('file.insert_step',path=str(R/'cad_solidcraft/build/cat/cat_shells.step'),name='Current CAT shells',matrix=[1,0,0,0,0,1,0,-50,0,0,1,68]);color(cat['bodies'],'#596775',.65)
 cm=c.execute('file.insert_step',path=str(R/'cad_solidcraft/exports/cat_mount.step'),name='Current CAT mount',matrix=[1,0,0,0,0,1,0,-50,0,0,1,68]);color(cm['bodies'],'#3b93b0')
 groups['reference_steel']=plate['bodies'];groups['reference_lidar']=lidar['bodies'];groups['reference_cat']=cat['bodies']+cm['bodies']
 finish_view()
 cam={'target':[0,42,90],'yaw':2.5,'pitch':.42,'distance':285,'fov':0}
 c.execute('view.save',name='Current sensor assembly',camera=cam)
 c.execute('view.save',name='Camera guard and double hooks',camera={'target':[0,100,76],'yaw':2.6,'pitch':.25,'distance':105,'fov':0})
 c.execute('view.save',name='Perforated U rim',camera={'target':[0,55,78],'yaw':2.4,'pitch':-.15,'distance':165,'fov':0})
 c.execute('view.apply',camera=cam)
 c.call('save',{'path':str(O/'lidar_camera_system.sc')})
 c.call('screenshot',{'path':str(O/'assembled.png'),'source':'model','camera':cam,'width':1500,'height':1100,'grid':False,'axes':False})
 (O/'groups.json').write_text(json.dumps(groups,indent=2));(O/'anchors.json').write_text(json.dumps(anchors))
 (O/'system_native.json').write_text(json.dumps(c.call('inspect_design'),ensure_ascii=False,indent=2))
 print('CURRENT DRAFT READY',flush=True)
