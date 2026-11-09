"""Current two-plate layout with the SolidCraft brass-standoff battery cradle.
Rear TOF interference remains unresolved and is reported by check_two_layer.py.
"""
import hashlib
import json
import math
import sys
if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
from cad_common import App, Part, ROOT, V, bounds, cat_shells

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
         ('cat_plate_t',3,'贴壳托板厚度'),
         ('cat_anchor_x',50,'CAT 落脚锚孔列 X；用户已确认 (±50)'),
         ('cat_anchor_y1',-88.39,'CAT 后落脚锚孔行 Y；用户已确认'),
         ('cat_anchor_y2',-11.47,'CAT 前落脚锚孔行 Y；用户已确认'),
         ('cat_foot_d',13,'落脚凸台直径；带孔凸台坐于铁板孔上'),
         ('cat_anchor_hole_d',3.0,'M3 锚孔打印补偿孔径（铁板孔 Ø3.2）'),
         ('lidar_y',55,'雷达中心 Y'),('lidar_lift',33,'雷达局部架高；让扫描头越过 CAT'),
         ('lidar_plate_t',3,'雷达概念托架顶板厚度'),
         ('battery_y',-102.9,'当前托架局部原点的世界 Y'),
         ('battery_lift',12.4,'铜柱 10 + 托架局部底面下沉 2.4；对应导入模型的局部坐标'),
         ('battery_floor_h',2,'当前模型承托面局部 Z'),
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

# Four candidate standoffs use source holes; availability remains unresolved.
# Rear wheel-group holes are unavailable and are no longer shown as layer supports.
# They are references for the layer structure, not approved installation choices.
posts=group('LayerPosts','层间 50 mm 铜柱候选 · 孔位占用待确认')
cyls=[f.Surface for f in steel.Faces if isinstance(f.Surface,Part.Cylinder)
      and abs(f.Surface.Axis.z)>.999 and abs(f.Surface.Radius-1.6)<.001]
post_objs=[];post_points=[]
for i,(x,y) in enumerate([(-50,81.61),(50,81.61),(-60,27.61),(60,27.61)],1):
    c=min(cyls,key=lambda c:math.hypot(c.Center.x-x,c.Center.y-y))
    assert math.hypot(c.Center.x-x,c.Center.y-y)<.02
    p=cylinder(posts,'LayerPost'+str(i),c.Center.x,c.Center.y,1.5,3,50)
    p.Label=f'层间铜柱候选 {i}（未确认可用孔）';p.setExpression('Height','Params.layer_gap')
    post_objs.append(p);post_points.append([c.Center.x,c.Center.y])

battery_group=group('BatteryGroup','当前铜柱版电池托架 · 后 TOF 干涉待解决',l1)
battery_group.Placement.Rotation=App.Rotation(V(0,0,1),-90)
battery_group.setExpression('Placement.Base.y','Params.battery_y')
battery_group.setExpression('Placement.Base.z','Params.base_z + Params.battery_lift')
cradle_shape=Part.read(str(ROOT/'cad_solidcraft/exports/battery_cradle.step'))
cradle=feature(battery_group,'BatteryCradle','铜柱版托架 · 均匀 4.4 mm 底板 / 1.2 mm 扎带槽',cradle_shape)
mount=Part.read(str(ROOT/'cad_solidcraft/exports/battery_mount.step'))
assert len(mount.Solids)==9
hardware=[]
for i,solid in enumerate(sorted([x for x in mount.Solids if x.Volume<10000],key=lambda x:(x.CenterOfMass.x,x.CenterOfMass.y,x.CenterOfMass.z)),1):
    label='M3×10+4 铜柱（名义包络）' if solid.Volume>100 else 'M3 螺母（名义包络）'
    hardware.append(feature(battery_group,'BatteryHardware'+str(i),label,solid))
budget=box(l1,'BatteryHeightEnvelope',-43.3,-134.2,15.9,86.6,62.6,33.6)
budget.Label='电池高度预算框 · 33.6 mm 上限 / 非实物'
budget.setExpression('Placement.Base.y','Params.battery_y - 31.3 mm')
budget.setExpression('Placement.Base.z','Params.base_z + Params.battery_lift + Params.battery_floor_h')
budget.setExpression('Height','Params.layer_gap - Params.battery_lift - Params.battery_floor_h - Params.battery_margin')

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
# Feet sit exactly on the user-approved plate anchors (±50, -88.39) and
# (±50, -11.47); each foot is a Ø13 boss with an M3 compensated through hole.
feet=[]
for i,(sx,sy,ynode) in enumerate([(-1,-1,'cat_anchor_y1'),(1,-1,'cat_anchor_y1'),(-1,1,'cat_anchor_y2'),(1,1,'cat_anchor_y2')],1):
    f=cylinder(cat_group,'CATFoot'+str(i),0,0,-13,6.5,10)
    f.Label='落脚凸台 Ø13 · 坐于已确认铁板锚孔'
    f.setExpression('Radius','Params.cat_foot_d / 2')
    f.setExpression('Height','Params.cat_lift - Params.cat_plate_t')
    f.setExpression('Placement.Base.x',f'{sx} * Params.cat_anchor_x')
    f.setExpression('Placement.Base.y',f'Params.{ynode} - Params.cat_y')
    f.setExpression('Placement.Base.z','-Params.cat_lift');feet.append(f)
fused_mount=fusion(cat_group,'CATMountFused','CAT 贴壳托板 + 四个锚孔落脚凸台',[tray]+feet)
anchor_cutters=[]
for i,(sx,sy,ynode) in enumerate([(-1,-1,'cat_anchor_y1'),(1,-1,'cat_anchor_y1'),(-1,1,'cat_anchor_y2'),(1,1,'cat_anchor_y2')],1):
    h=cylinder(cat_group,'CATAnchorHole'+str(i),0,0,-13.5,1.5,10.5)
    h.Label='M3 锚孔 Ø3.0（Ø3.2 铁板孔补偿）'
    h.setExpression('Radius','Params.cat_anchor_hole_d / 2')
    h.setExpression('Placement.Base.x',f'{sx} * Params.cat_anchor_x')
    h.setExpression('Placement.Base.y',f'Params.{ynode} - Params.cat_y')
    h.setExpression('Placement.Base.z','-Params.cat_lift - 0.5 mm');anchor_cutters.append(h)
holes_mount=doc.addObject('Part::MultiFuse','CATAnchorHoles');cat_group.addObject(holes_mount)
holes_mount.Shapes=anchor_cutters;doc.recompute()
cat_mount=doc.addObject('Part::Cut','CATMount');cat_group.addObject(cat_mount)
cat_mount.Label='CAT 贴壳托板连接件 · 脚位已确认 · 保留 8 通风槽 + 6 固定孔'
cat_mount.Base=fused_mount;cat_mount.Tool=holes_mount

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

# Confirmed anchors: read back the compensated holes from the final solids and
# verify they sit on the approved plate grid; verify nut protrusion zones in
# layer 1 stay clear of the C30D board and the battery envelope.
approved_cat=[(sx*50,y,50) for sx in (-1,1) for y in (-88.39,-11.47)]
cat_holes=[]
for f in cat_mount.Shape.Faces:
    if isinstance(f.Surface,Part.Cylinder) and abs(f.Surface.Radius-1.5)<.01:
        c=f.Surface.Center
        v=cat_group.Placement.multVec(V(c.x,c.y,c.z))
        cat_holes.append((v.x,v.y))
for ax,ay,_ in approved_cat:
    assert min(math.hypot(hx-ax,hy-ay) for hx,hy in cat_holes)<.02,(ax,ay,cat_holes)
approved_bat=[(-43,-128.47),(43,-128.47),(-39.04,-77.33),(39.04,-77.33)]
bat_holes_g=[]
for f in cradle.Shape.Faces:
    if isinstance(f.Surface,Part.Cylinder) and abs(f.Surface.Radius-1.65)<.01:
        c=f.Surface.Center
        v=battery_group.Placement.multVec(V(c.x,c.y,c.z))
        bat_holes_g.append((v.x,v.y))
for ax,ay in approved_bat:
    assert min(math.hypot(hx-ax,hy-ay) for hx,hy in bat_holes_g)<.02,(ax,ay,bat_holes_g)
driver_bb=driver.BoundBox
budget_bb=global_shape(budget).BoundBox
# Nut + protruding bolt below the upper plate occupy roughly z 45.5..51.5.
nut_z_min=51.5-6.0
for ax,ay in [(x[0],x[1]) for x in approved_cat]:
    fastener_r=2.75
    in_x=(ax+fastener_r>driver_bb.XMin and ax-fastener_r<driver_bb.XMax)
    in_y=(ay+fastener_r>driver_bb.YMin and ay-fastener_r<driver_bb.YMax)
    # XY overlap only matters if the device reaches into the nut zone vertically.
    assert not(in_x and in_y and driver_bb.ZMax>nut_z_min),(ax,ay,'C30D nut zone clash')
    in_x=(ax+fastener_r>budget_bb.XMin and ax-fastener_r<budget_bb.XMax)
    in_y=(ay+fastener_r>budget_bb.YMin and ay-fastener_r<budget_bb.YMax)
    assert not(in_x and in_y and budget_bb.ZMax>nut_z_min),(ax,ay,'battery envelope nut zone clash')

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
visible += hardware
visible += [doc.getObject('MCUSpacer'+str(i)) for i in range(1,5)]
for o in doc.Objects:
    if hasattr(o,'Visibility'):o.Visibility=False
for g in [l1,l2,posts,battery_group,front_group,rear_group,cat_group,lidar_group,camera_group]:g.Visibility=True
for o in visible:o.Visibility=True
doc.recompute()
path=ROOT/'assemblies/two_layer.FCStd'
doc.saveAs(str(path))
report={'status':'assembly_conflict_rear_tof_unresolved',
        'architecture':{'plates':'two identical existing steel chassis plates','plate_thickness_mm':1.5,
                        'layer_gap_mm':50,'lower_devices':['FrontTOF','RearTOF','C30D','BatteryCradle'],
                        'upper_devices':['CAT','Lidar','Camera']},
        'datums_mm':{'lower_plate_top':1.5,'upper_plate_bottom':51.5,'upper_plate_top':53,
                     'cat_bottom':66,'cat_top':cat_top,'lidar_base':86,'lidar_scan_head_lowest':lidar_head_low},
        'checks':{'identical_steel_plate_symmetric_difference_mm3':plate_difference,
                  'lidar_head_above_cat_mm':lidar_head_low-cat_top,
                  'candidate_posts_vs_cradle_overlap_mm3':post_overlaps,
                  'cat_vent_count':8,'cat_vents_clear':True,'layer_gap_parameter_test':'pass',
                  'confirmed_anchor_holes_readback':'pass',
                  'nut_zone_clearance_c30d_and_battery':'pass'},
        'confirmed_fixtures':{'battery_cradle':{'anchors_xy':approved_bat,'hole_d_mm':3.3,
                                                   'fastener':'M3×10+4 铜柱 + M3 螺母；底部紧固件长度待选',
                                                   'note':'铜柱对边 5.5、螺母对边 5.5/高 2.4 为名义值；后 TOF 干涉未解决'},
                              'cat_mount':{'anchors_xy':[(p[0],p[1]) for p in approved_cat],'foot_d_mm':13,'hole_d_mm':3.0,
                                           'fastener':'M3 对锁 + 底面螺母'}},
        'battery_height_budget_mm':{'support_z':15.9,'available_height':35.6,'clearance_budget':2,'max_battery_height':33.6},
        'candidate_layer_post_xy_unconfirmed':post_points,
        'objects':{k:bounds(v) for k,v in shapes.items()},
        'reference_limitations':{'CAT':'Only metal shells are positioned; external antennas and cables are not included in shell-clearance claims',
                                 'rear_tof':'Source is a valid compound of shells, not solid; only reference/envelope checks apply',
                                 'camera':'Board outline 29×31.25 and hole pitch 23×24 from V1R1 drawing; thickness/lens are placeholders',
                                 'lidar':'Original fixed curved cable solids hidden; final cable route still required',
                                 'battery':'No actual battery solid or confirmed height; reference cradle preserved'},
        'known_conflicts':['RearTOF intersects the current battery floor at the existing placement; do not treat this assembly as installation-ready'],
        'not_tested':['Physical nut/bolt access under both plates (user to verify ground clearance)',
                      'Lidar and camera mounts (deferred by user until CAT/battery are fixed)',
                      'All remaining fastener retention details',
                      'Actual battery height and camera thickness/lens geometry','Cable routing and full FOV/access',
                      'Strength, vibration, steel-plate deflection, print fit and temperature'],
        'visible_object_names':[o.Name for o in visible],
        'battery_source_sha256':hashlib.sha256((ROOT/'cad_solidcraft/exports/battery_cradle.step').read_bytes()).hexdigest(),
        'sources':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (ROOT/'models').glob('*') if p.suffix.lower() in ['.step','.stp']}}
with open(OUT/'two_layer_checks.json','w',encoding='utf-8') as fh:
    fh.write(json.dumps(report,ensure_ascii=False,indent=2))
App.closeDocument(doc.Name)
saved=App.openDocument(str(path));saved.recompute()
assert abs(global_shape(saved.getObject('UpperSteelPlate')).BoundBox.ZMin-51.5)<1e-6
assert abs(saved.getObject('Params').layer_gap.Value-50)<1e-6
assert not [o.Name for o in saved.Objects if any('Error' in str(s) or 'Invalid' in str(s) for s in o.State)]
# CAT exports remain here; battery printable outputs are in cad_solidcraft/exports.
import Mesh
import MeshPart
exports=ROOT/'output/two_layer'
for sub in ['step','stl']:(exports/sub).mkdir(parents=True,exist_ok=True)
for name,label,fn in [('CATMount','CAT托板连接件','cat_mount')]:
    obj=saved.getObject(name);shape=global_shape(obj)
    assert shape.isValid() and shape.isClosed() and len(shape.Solids)==1,name
    shape.exportStep(str(exports/'step'/f'{fn}.step'))
    mesh=MeshPart.meshFromShape(Shape=shape,LinearDeflection=0.15,AngularDeflection=0.3)
    mesh.write(str(exports/'stl'/f'{fn}.stl'))
print(json.dumps({'output':str(path),'checks':report['checks'],'datums':report['datums_mm'],'saved_readback':'pass',
                  'exports':{'battery':str(ROOT/'cad_solidcraft/exports/battery_cradle.step'),
                             'cat_mount':str(exports/'step'/'cat_mount.step')}},ensure_ascii=True,indent=2),flush=True)
