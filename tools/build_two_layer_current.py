"""Current two-steel-plate layout. Draft adapters have no chosen chassis holes."""
import hashlib
import json
import math
from cad_common import App, Part, ROOT, V, bounds, cat_shells, battery_cradle

OUT=ROOT/'output/two_layer'
OUT.mkdir(parents=True,exist_ok=True)


def global_shape(obj):
    s=obj.Shape.copy()
    s.Placement=obj.getGlobalPlacement().multiply(obj.Placement.inverse()).multiply(s.Placement)
    return s


baseline=App.openDocument(str(ROOT/'assemblies/c30d_on_chassis.FCStd'))
chassis=global_shape(baseline.getObject('Chassis_R3mini'))
driver=global_shape(baseline.getObject('C30D_V2_2'))
mcu_spacers=[global_shape(baseline.getObject('Spacer'+str(i))) for i in range(1,5)]
App.closeDocument(baseline.Name)
steel=max([s for s in chassis.Solids if s.BoundBox.ZLength<2],key=lambda s:s.Volume).copy()
assert abs(steel.BoundBox.ZLength-1.5)<1e-6

doc=App.newDocument('R3_TwoLayer')
doc.Label='当前两层：两块相同铁板 · 下层电控 / 上层感知'
params=doc.addObject('Spreadsheet::Sheet','Params')
entries=[('base_z',1.5,'下层铁板上表面'),('plate_t',1.5,'两块铁板厚度相同'),
         ('layer_gap',50,'层间铜柱高度；用户确认先用 50 mm'),
         ('cat_y',-50,'CAT 中心 Y'),('cat_lift',13,'第二层板面到 CAT 底面'),
         ('cat_plate_t',3,'贴壳托板厚度'),('cat_foot_d',10,'四个示意落脚直径'),
         ('cat_foot_spanx',112,'示意落脚 X 跨距；未定安装孔'),
         ('cat_foot_spany',60,'示意落脚 Y 跨距；未定安装孔'),
         ('lidar_y',55,'雷达中心 Y'),('lidar_lift',33,'雷达局部架高；让扫描头越过 CAT'),
         ('lidar_plate_t',3,'雷达概念托架顶板厚度'),
         ('battery_y',-84,'电池托架中心 Y'),('battery_floor_h',2,'参考托架承托面离其底面'),
         ('battery_margin',2,'电池到上层铁板的高度预算余量'),
         ('tof_front_y',111,'前 TOF 光学面 Y'),('tof_front_z',22,'前 TOF 中心高度'),
         ('tof_rear_y',-132,'后 TOF PCB 原点 Y'),('tof_rear_z',12.5,'后 TOF 原点高度'),
         ('camera_y',104,'相机 PCB 平面 Y'),('camera_base',3,'相机 PCB 底边离二层板面'),
         ('camera_pcb_t',1.2,'相机板厚占位，未实测'),('camera_lens_r',6,'镜头半径占位，未实测'),
         ('camera_lens_depth',8,'镜头深度占位，未实测')]
params.set('A1','Parameter');params.set('B1','Value');params.set('C1','Meaning')
for row,(name,val,note) in enumerate(entries,2):
    params.set(f'A{row}',name);params.set(f'B{row}',f'={val} mm')
    params.setAlias(f'B{row}',name);params.set(f'C{row}',note)
doc.recompute()


def group(name,label,parent=None):
    g=doc.addObject('App::Part',name);g.Label=label
    if parent:parent.addObject(g)
    return g


def feature(parent,name,label,shape):
    o=doc.addObject('Part::Feature',name);o.Label=label;o.Shape=shape;parent.addObject(o);return o


def box(parent,name,x,y,z,l,w,h):
    o=doc.addObject('Part::Box',name);parent.addObject(o)
    o.Length=l;o.Width=w;o.Height=h;o.Placement.Base=V(x,y,z);return o


def cylinder(parent,name,x,y,z,r,h):
    o=doc.addObject('Part::Cylinder',name);parent.addObject(o)
    o.Radius=r;o.Height=h;o.Placement.Base=V(x,y,z);return o


def fusion(parent,name,label,objects):
    o=doc.addObject('Part::MultiFuse',name);parent.addObject(o);o.Label=label;o.Shapes=objects
    doc.recompute();assert o.Shape.isValid() and len(o.Shape.Solids)==1
    return o


l1=group('Layer1','第一层：铁底板 / 前后 TOF / C30D / 电池')
l2=group('Layer2','第二层：同款铁板 / CAT / 雷达 / 相机')
l2.setExpression('Placement.Base.z','Params.base_z + Params.layer_gap')
feature(l1,'Chassis','下层原有铁底盘及轮组',chassis)
feature(l1,'C30D','C30D MCU · 已确定 6 mm 垫高',driver)
for i,s in enumerate(mcu_spacers,1):feature(l1,'MCUSpacer'+str(i),'MCU 铜柱',s)
upper=feature(l2,'UpperSteelPlate','第二块相同铁底板 · 原轮廓 / 原孔型',steel)
upper.addProperty('App::PropertyString','MaterialNote').MaterialNote='用户现有铁板；源模型厚度 1.5 mm'

# Six candidate standoffs use actual common holes, but availability is unresolved.
# They are references for the layer structure, not approved installation choices.
posts=group('LayerPosts','层间 50 mm 铜柱候选 · 孔位占用待确认')
cyls=[f.Surface for f in steel.Faces if isinstance(f.Surface,Part.Cylinder)
      and abs(f.Surface.Axis.z)>.999 and abs(f.Surface.Radius-1.6)<.001]
post_objs=[];post_points=[]
for i,(x,y) in enumerate([(-50,81.61),(50,81.61),(-60,27.61),(60,27.61),(-50,-118.39),(50,-118.39)],1):
    c=min(cyls,key=lambda c:math.hypot(c.Center.x-x,c.Center.y-y))
    assert math.hypot(c.Center.x-x,c.Center.y-y)<.02
    p=cylinder(posts,'LayerPost'+str(i),c.Center.x,c.Center.y,1.5,3,50)
    p.Label=f'层间铜柱候选 {i}（未确认可用孔）';p.setExpression('Height','Params.layer_gap')
    post_objs.append(p);post_points.append([c.Center.x,c.Center.y])

battery_group=group('BatteryGroup','电池参考托架 · 原孔待调整',l1)
battery_group.Placement.Rotation=App.Rotation(V(0,0,1),90)
battery_group.setExpression('Placement.Base.y','Params.battery_y')
battery_group.setExpression('Placement.Base.z','Params.base_z')
cradle=feature(battery_group,'BatteryCradle','用户指定托架 · 内腔与夹持结构保留',battery_cradle())
budget=box(l1,'BatteryHeightEnvelope',-43.3,-112.5,3.5,86.6,57,46)
budget.Label='电池高度预算框 · 非实物电池模型'
budget.setExpression('Placement.Base.y','Params.battery_y - 28.5 mm')
budget.setExpression('Placement.Base.z','Params.base_z + Params.battery_floor_h')
budget.setExpression('Height','Params.layer_gap - Params.battery_floor_h - Params.battery_margin')

front_group=group('FrontTOFGroup','第一层前 TOF-M · 朝 +Y',l1)
front_group.Placement.Rotation=App.Rotation(V(1,0,0),-90).multiply(App.Rotation(V(0,0,1),90))
front_group.setExpression('Placement.Base.y','Params.tof_front_y')
front_group.setExpression('Placement.Base.z','Params.tof_front_z')
front=feature(front_group,'FrontTOF','TOF-M S 厂家模型',Part.read(str(ROOT/'models/TOFSense_M_S_Appearance_V1.0.step')))
rear_group=group('RearTOFGroup','第一层后 TOF-F2 · 朝 -Y',l1)
rear_group.Placement.Rotation=App.Rotation(V(1,0,0),90)
rear_group.setExpression('Placement.Base.y','Params.tof_rear_y')
rear_group.setExpression('Placement.Base.z','Params.tof_rear_z')
rear_shape=Part.read(str(ROOT/'models/TOFSense_F2_Mini_Appearance_V1.0.step'))
rear=feature(rear_group,'RearTOF','TOF-F2 厂家曲面参考 · 非闭合实体',rear_shape)

cat_group=group('CATGroup','第二层 CAT 与贴壳连接件概念',l2)
cat_group.setExpression('Placement.Base.y','Params.cat_y')
cat_group.setExpression('Placement.Base.z','Params.plate_t + Params.cat_lift')
shells,face=cat_shells()
cat_shell_objs=[feature(cat_group,'CATShell'+str(i),'CAT 金属外壳',s) for i,s in enumerate(shells)]
profile=feature(cat_group,'CATBottomProfile','CAT 底面原 8 通风槽 + 6 安装孔',face)
tray=doc.addObject('Part::Extrusion','CATContactPlate');cat_group.addObject(tray)
tray.Base=profile;tray.DirMode='Custom';tray.Dir=V(0,0,-1);tray.Solid=True
tray.setExpression('LengthFwd','Params.cat_plate_t')
feet=[]
for i,(sx,sy) in enumerate([(-1,-1),(1,-1),(-1,1),(1,1)],1):
    f=cylinder(cat_group,'CATFoot'+str(i),sx*56,sy*30,-13,5,10)
    f.setExpression('Radius','Params.cat_foot_d / 2')
    f.setExpression('Height','Params.cat_lift - Params.cat_plate_t')
    f.setExpression('Placement.Base.x',f'{sx} * Params.cat_foot_spanx / 2')
    f.setExpression('Placement.Base.y',f'{sy} * Params.cat_foot_spany / 2')
    f.setExpression('Placement.Base.z','-Params.cat_lift');feet.append(f)
cat_mount=fusion(cat_group,'CATMount','CAT 贴壳托板 + 四个局部落脚 · 未开底盘锚孔',[tray]+feet)

lidar_source=Part.read(str(ROOT/'models/单线雷达总装.STEP'))
# Keep the attached connector that reaches the device body. Only the remote
# cable tail and its loose end connectors are hidden pending actual routing.
main_solids=[s.copy() for s in lidar_source.Solids if s.BoundBox.YMax>=-40]
wire_solids=[s.copy() for s in lidar_source.Solids if s.BoundBox.YMax<-40]
main=Part.makeCompound(main_solids)
lidar_seat=main.BoundBox.ZMin
scan_lower=min(s.BoundBox.ZMin for s in main_solids if s.BoundBox.ZMax>20)-lidar_seat
main.translate(V(0,0,-lidar_seat))
lidar_group=group('LidarGroup','第二层雷达 · 扫描头抬过 CAT 壳顶',l2)
lidar_group.setExpression('Placement.Base.y','Params.lidar_y')
lidar_group.setExpression('Placement.Base.z','Params.plate_t + Params.lidar_lift')
lidar=feature(lidar_group,'Lidar','雷达机身与扫描头（原弯曲线缆另列）',main)
cables=Part.makeCompound(wire_solids);cables.translate(V(0,0,-lidar_seat))
wire_ref=feature(lidar_group,'LidarCableReference','原模型线缆形状 · 待重新走线 · 默认隐藏',cables)
platform=box(lidar_group,'LidarPlatform',-36,-40,-3,72,80,3)
platform.setExpression('Height','Params.lidar_plate_t')
platform.setExpression('Placement.Base.z','-Params.lidar_plate_t')
lidar_feet=[]
for i,(x,y) in enumerate([(-26,-28),(26,-28),(-26,28),(26,28)],1):
    f=cylinder(lidar_group,'LidarFoot'+str(i),x,y,-33,5,30)
    f.setExpression('Height','Params.lidar_lift - Params.lidar_plate_t')
    f.setExpression('Placement.Base.z','-Params.lidar_lift');lidar_feet.append(f)
lidar_mount=fusion(lidar_group,'LidarMount','雷达转接架占位 · 保持原机身 · 紧固与锚孔未定',[platform]+lidar_feet)

camera_group=group('CameraGroup','第二层前缘相机 · 朝 +Y · 镜头占位',l2)
camera_group.setExpression('Placement.Base.y','Params.camera_y')
camera_group.setExpression('Placement.Base.z','Params.plate_t + Params.camera_base')
pcb=Part.makeBox(29,1.2,31.25,V(-14.5,0,0))
for x in [-11.5,11.5]:
    for z in [3.625,27.625]:pcb=pcb.cut(Part.makeCylinder(1.25,1.2,V(x,0,z),V(0,1,0)))
cam_pcb=feature(camera_group,'CameraPCB','IMX415 V1R1 板轮廓/孔位 · 厚度未实测',pcb)
lens=cylinder(camera_group,'CameraLensEnvelope',0,1.2,15.625,6,8)
lens.Label='镜头包络占位 · 尺寸不是加工依据'
lens.Placement.Rotation=App.Rotation(V(0,0,1),V(0,1,0))
lens.setExpression('Radius','Params.camera_lens_r');lens.setExpression('Height','Params.camera_lens_depth')
cam_base=Part.makeBox(44,14,3,V(-22,-14,-3))
cam_wall=Part.makeBox(34,3,35.5,V(-17,-3,-3))
cam_frame=cam_base.fuse(cam_wall).removeSplitter()
for x in [-11.5,11.5]:
    for z in [3.625,27.625]:cam_frame=cam_frame.cut(Part.makeCylinder(1.4,3,V(x,-3,z),V(0,1,0)))
camera_mount=feature(camera_group,'CameraMount','相机支架概念 · 无铁板锚孔',cam_frame)
doc.recompute()

# Read geometry in the document coordinate system, including all parent groups.
shapes={o.Name:global_shape(o) for o in [upper,front,rear,cradle,budget,cat_mount,lidar,lidar_mount,cam_pcb,lens,camera_mount]+cat_shell_objs}
for o in [cat_mount,lidar_mount,camera_mount]:
    assert o.Shape.isValid() and o.Shape.isClosed() and len(o.Shape.Solids)==1,o.Name
assert abs(shapes['UpperSteelPlate'].BoundBox.ZMin-51.5)<1e-6
assert abs(shapes['UpperSteelPlate'].BoundBox.ZMax-53)<1e-6
upper_local=shapes['UpperSteelPlate'].copy();upper_local.translate(V(0,0,-51.5))
plate_difference=upper_local.cut(steel).Volume+steel.cut(upper_local).Volume
assert plate_difference<1e-5
for s in [global_shape(front),global_shape(rear),global_shape(cradle),driver]:
    assert s.BoundBox.ZMax<51.5
post_overlaps=[]
for p in post_objs:
    s=global_shape(p)
    # Candidate rear posts overlap the cradle bbox, so test the actual cradle.
    post_overlaps.append(s.common(global_shape(cradle)).Volume)
    assert s.BoundBox.XMax<driver.BoundBox.XMin or s.BoundBox.XMin>driver.BoundBox.XMax or s.BoundBox.YMin>driver.BoundBox.YMax or s.BoundBox.YMax<driver.BoundBox.YMin
assert max(post_overlaps)<1e-5,post_overlaps
cat_top=max(global_shape(o).BoundBox.ZMax for o in cat_shell_objs)
lidar_head_low=lidar_group.getGlobalPlacement().Base.z+scan_lower
assert lidar_head_low-cat_top>5
vent_wires=[w for w in face.Wires if w.BoundBox.XLength>20 and w.BoundBox.YLength<5]
assert len(vent_wires)==8
for w in vent_wires:
    column=Part.Face(w).extrude(V(0,0,-13))
    assert column.common(cat_mount.Shape).Volume<1e-5

# A real parameter exercise: changing the tier gap moves the full second layer,
# changes the candidate standoffs and battery budget, and leaves layer 1 fixed.
cell=params.getCellFromAlias('layer_gap')
original_cat=global_shape(cat_shell_objs[0]).BoundBox.ZMin
original_driver=global_shape(doc.getObject('C30D')).BoundBox.ZMin
params.set(cell,'=60 mm');doc.recompute()
assert abs(global_shape(upper).BoundBox.ZMin-61.5)<1e-6
assert abs(global_shape(cat_shell_objs[0]).BoundBox.ZMin-original_cat-10)<1e-6
assert abs(global_shape(doc.getObject('C30D')).BoundBox.ZMin-original_driver)<1e-6
assert all(abs(p.Height.Value-60)<1e-6 for p in post_objs)
params.set(cell,'=50 mm');doc.recompute()

visible=[doc.getObject('Chassis'),doc.getObject('C30D'),upper,front,rear,cradle,budget,cat_mount,lidar,lidar_mount,cam_pcb,lens,camera_mount]+cat_shell_objs+post_objs
visible += [doc.getObject('MCUSpacer'+str(i)) for i in range(1,5)]
for o in doc.Objects:
    if hasattr(o,'Visibility'):o.Visibility=False
for g in [l1,l2,posts,battery_group,front_group,rear_group,cat_group,lidar_group,camera_group]:g.Visibility=True
for o in visible:o.Visibility=True
doc.recompute()
path=ROOT/'assemblies/two_layer.FCStd'
doc.saveAs(str(path))
report={'status':'geometry_layout_checked_not_manufacturing_ready',
        'architecture':{'plates':'two identical existing steel chassis plates','plate_thickness_mm':1.5,
                        'layer_gap_mm':50,'lower_devices':['FrontTOF','RearTOF','C30D','BatteryCradle'],
                        'upper_devices':['CAT','Lidar','Camera']},
        'datums_mm':{'lower_plate_top':1.5,'upper_plate_bottom':51.5,'upper_plate_top':53,
                     'cat_bottom':66,'cat_top':cat_top,'lidar_base':86,'lidar_scan_head_lowest':lidar_head_low},
        'checks':{'identical_steel_plate_symmetric_difference_mm3':plate_difference,
                  'lidar_head_above_cat_mm':lidar_head_low-cat_top,
                  'candidate_posts_vs_cradle_overlap_mm3':post_overlaps,
                  'cat_vent_count':8,'cat_vents_clear':True,'layer_gap_parameter_test':'pass'},
        'battery_height_budget_mm':{'support_z':3.5,'available_height':48,'clearance_budget':2,'max_battery_height':46},
        'candidate_layer_post_xy_unconfirmed':post_points,
        'objects':{k:bounds(v) for k,v in shapes.items()},
        'reference_limitations':{'CAT':'Only metal shells are positioned; external antennas and cables are not included in shell-clearance claims',
                                 'rear_tof':'Source is a valid compound of shells, not solid; only reference/envelope checks apply',
                                 'camera':'Board outline 29×31.25 and hole pitch 23×24 from V1R1 drawing; thickness/lens are placeholders',
                                 'lidar':'Original fixed curved cable solids hidden; final cable route still required',
                                 'battery':'No actual battery solid or confirmed height; reference cradle preserved'},
        'not_tested':['Physical availability of all new mounting holes','All fasteners and retention details',
                      'Actual battery height and camera thickness/lens geometry','Cable routing and full FOV/access',
                      'Strength, vibration, steel-plate deflection, print fit and temperature'],
        'visible_object_names':[o.Name for o in visible],
        'sources':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (ROOT/'models').glob('*') if p.suffix.lower() in ['.step','.stp']}}
(OUT/'two_layer_checks.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
App.closeDocument(doc.Name)
saved=App.openDocument(str(path));saved.recompute()
assert abs(global_shape(saved.getObject('UpperSteelPlate')).BoundBox.ZMin-51.5)<1e-6
assert abs(saved.getObject('Params').layer_gap.Value-50)<1e-6
assert not [o.Name for o in saved.Objects if any('Error' in str(s) or 'Invalid' in str(s) for s in o.State)]
print(json.dumps({'output':str(path),'checks':report['checks'],'datums':report['datums_mm'],'saved_readback':'pass'},ensure_ascii=False,indent=2),flush=True)
