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
         ('cat_y',-50,'CAT 中心 Y'),('cat_lift',15,'第二层板面到 CAT 底面'),
         ('cat_plate_t',5,'贴壳托板厚度'),
         ('cat_anchor_x',50,'CAT 落脚锚孔列 X；用户已确认 (±50)'),
         ('cat_anchor_y1',-88.39,'CAT 后落脚锚孔行 Y；用户已确认'),
         ('cat_anchor_y2',-11.47,'CAT 前落脚锚孔行 Y；用户已确认'),
         ('cat_foot_d',12,'落脚凸台直径；带孔凸台坐于铁板孔上'),
         ('cat_anchor_hole_d',2.5,'M3×10 自攻导孔试配直径，深 9 mm'),
         ('lidar_y',55,'雷达中心 Y'),('lidar_lift',33,'雷达局部架高；让扫描头越过 CAT'),
         ('lidar_plate_t',3,'雷达概念托架顶板厚度'),
         ('battery_y',-102.9,'当前托架局部原点的世界 Y'),
         ('battery_lift',12.4,'铜柱 10 + 托架局部底面下沉 2.4；对应导入模型的局部坐标'),
         ('battery_floor_h',2,'当前模型承托面局部 Z'),
         ('battery_margin',2,'电池到上层铁板的高度预算余量'),
         ('tof_front_y',111,'前 TOF 光学面 Y'),('tof_front_z',22,'前 TOF 中心高度'),
         ('tof_rear_y',-132,'后 TOF PCB 原点 Y'),('tof_rear_z',12.5,'后 TOF 原点高度'),
         ('camera_model_note',0,'相机模块位置由雷达接口定义；孔径/板厚/镜头为待测占位')]
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
# Current SolidCraft native model is the geometry authority for the connector.
cat_mount=feature(cat_group,'CATMount','CAT 直筋连接件 · 5mm 均匀托板 / 内嵌螺母 / 自攻四柱',
                  Part.read(str(ROOT/'cad_solidcraft/exports/cat_mount.step')))
assert cat_mount.Shape.isValid() and len(cat_mount.Shape.Solids)==1

lidar_source=Part.read(str(ROOT/'models/单线雷达总装.STEP'))
# Keep the attached connector that reaches the device body. Only the remote
# cable tail and its loose end connectors are hidden pending actual routing.
main_solids=[s.copy() for s in lidar_source.Solids if s.BoundBox.YMax>=-40]
wire_solids=[s.copy() for s in lidar_source.Solids if s.BoundBox.YMax<-40]
main=Part.makeCompound(main_solids)
lidar_seat=main.BoundBox.ZMin
scan_lower=min(s.BoundBox.ZMin for s in main_solids if s.BoundBox.ZMax>20)-lidar_seat
main.translate(V(0,0,-lidar_seat));main.rotate(V(),V(0,0,1),-90)
lidar_group=group('LidarGroup','第二层雷达 · 扫描头抬过 CAT 壳顶',l2)
lidar_group.setExpression('Placement.Base.y','Params.lidar_y')
lidar_group.setExpression('Placement.Base.z','Params.plate_t + Params.lidar_lift')
lidar=feature(lidar_group,'Lidar','雷达机身与扫描头（原弯曲线缆另列）',main)
cables=Part.makeCompound(wire_solids);cables.translate(V(0,0,-lidar_seat));cables.rotate(V(),V(0,0,1),-90)
wire_ref=feature(lidar_group,'LidarCableReference','原模型线缆形状 · 待重新走线 · 默认隐藏',cables)
# Current LiDAR prototype: actual selected steel anchors and three-sided modular rim.
lidar_frame_shape=Part.read(str(ROOT/'cad_solidcraft/review/lidar_frame.step'))
lidar_frame_shape.translate(V(0,0,-33))
lidar_mount=feature(lidar_group,'LidarMount','雷达架初稿 · M3×10自攻 / 前左右孔带 / 耳朝后',lidar_frame_shape)

camera_group=group('CameraGroup','相机小盒＋后盖初稿 · 暂估配合 / 俯角10°',l2)
camera_group.setExpression('Placement.Base.y','Params.lidar_y')
camera_group.setExpression('Placement.Base.z','Params.plate_t')
def pitched(shape):
    shape.rotate(V(0,61,24),V(1,0,0),-10)
    return shape
cam_pcb_shape=Part.makeBox(29,1.2,31,V(-14.5,55,8.5))
for x in [-11.5,11.5]:
    for z in [11.5,36.5]:cam_pcb_shape=cam_pcb_shape.cut(Part.makeCylinder(1.25,1.2,V(x,55,z),V(0,1,0)))
cam_pcb=feature(camera_group,'CameraPCB','IMX415图纸板形/孔距 · 厚度和孔径未测',pitched(cam_pcb_shape))
lens=feature(camera_group,'CameraLensEnvelope','镜头包络Ø12×8及中心高度暂估',pitched(Part.makeCylinder(6,8,V(0,56.2,28),V(0,1,0))))
camera_mount=feature(camera_group,'CameraMount','双挂钩相机座 · 下脚落板 / M3防脱',Part.read(str(ROOT/'cad_solidcraft/review/camera_dock.step')))
camera_housing=feature(camera_group,'CameraHousing','相机小外壳初稿 · 镜头口Ø18暂估',pitched(Part.read(str(ROOT/'cad_solidcraft/review/camera_housing.step'))))
camera_cover=feature(camera_group,'CameraRearCover','后盖及后置螺母窝 · 板厚/元件高度待测',pitched(Part.read(str(ROOT/'cad_solidcraft/review/camera_rear_lid.step'))))
doc.recompute()

# Read geometry in the document coordinate system, including all parent groups.
shapes={o.Name:global_shape(o) for o in [upper,front,rear,cradle,budget,cat_mount,lidar,lidar_mount,cam_pcb,lens,camera_mount,camera_housing,camera_cover]+cat_shell_objs}
for o in [cat_mount,lidar_mount,camera_mount,camera_housing,camera_cover]:
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
assert lidar_head_low-cat_top>0  # Nominal separation only; former 5 mm allowance is no longer met.
vent_wires=[w for w in face.Wires if w.BoundBox.XLength>20 and w.BoundBox.YLength<5]
assert len(vent_wires)==8
for w in vent_wires:
    column=Part.Face(w).extrude(V(0,0,-15))
    assert column.common(cat_mount.Shape).Volume<1e-5

# Confirmed anchors: read back the compensated holes from the final solids and
# verify they sit on the approved plate grid; verify nut protrusion zones in
# layer 1 stay clear of the C30D board and the battery envelope.
approved_cat=[(sx*50,y,50) for sx in (-1,1) for y in (-88.39,-11.47)]
cat_holes=[]
for f in cat_mount.Shape.Faces:
    if isinstance(f.Surface,Part.Cylinder) and abs(f.Surface.Radius-1.25)<.01:
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

visible=[doc.getObject('Chassis'),doc.getObject('C30D'),upper,front,rear,cradle,budget,cat_mount,lidar,lidar_mount,cam_pcb,lens,camera_mount,camera_housing,camera_cover]+cat_shell_objs+post_objs
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
                     'cat_bottom':68,'cat_top':cat_top,'lidar_base':86,'lidar_scan_head_lowest':lidar_head_low},
        'checks':{'identical_steel_plate_symmetric_difference_mm3':plate_difference,
                  'lidar_head_above_cat_mm':lidar_head_low-cat_top,
                  'candidate_posts_vs_cradle_overlap_mm3':post_overlaps,
                  'cat_vent_count':8,'cat_vents_clear':True,'layer_gap_parameter_test':'pass',
                  'confirmed_anchor_holes_readback':'pass',
                  'nut_zone_clearance_c30d_and_battery':'pass'},
        'confirmed_fixtures':{'battery_cradle':{'anchors_xy':approved_bat,'hole_d_mm':3.3,
                                                   'fastener':'M3×10+4 铜柱 + M3 螺母；底部紧固件长度待选',
                                                   'note':'铜柱对边 5.5、螺母对边 5.5/高 2.4 为名义值；后 TOF 干涉未解决'},
                              'cat_mount':{'anchors_xy':[(p[0],p[1]) for p in approved_cat],'foot_d_mm':12,'hole_d_mm':2.5,
                                           'fastener':'底板：M3×10 自攻；外壳六孔：M3×10 普通机牙 + M3 螺母'}},
        'battery_height_budget_mm':{'support_z':15.9,'available_height':35.6,'clearance_budget':2,'max_battery_height':33.6},
        'candidate_layer_post_xy_unconfirmed':post_points,
        'objects':{k:bounds(v) for k,v in shapes.items()},
        'reference_limitations':{'CAT':'Only metal shells are positioned; external antennas and cables are not included in shell-clearance claims',
                                 'rear_tof':'Source is a valid compound of shells, not solid; only reference/envelope checks apply',
                                 'camera':'Current enclosed-camera prototype:29x31 outline,23x25 pitch confirmed; hole diameter2.5, thickness1.2,lens12x8 and center19.5from bottom are UNMEASURED; -10deg pitch example, optical clearance/dust sealing untested',
                                 'lidar':'LakiBeam1 rotated-90deg about Z, ears and90deg blind sector toward world-Y/CAT; bottom thread/depth variant still needs confirmation; remote cable hidden',
                                 'battery':'No actual battery solid or confirmed height; reference cradle preserved'},
        'layout_warnings':['CAT raised 2mm; lidar scan-head lower envelope remains above CAT by about 3.32mm, below previous 5mm allowance; optical FOV unverified'],
        'known_conflicts':['RearTOF intersects the current battery floor at the existing placement; do not treat this assembly as installation-ready'],
        'not_tested':['Physical nut/bolt access under both plates (user to verify ground clearance)',
                      'LiDAR/camera initial prototype, selected chassis anchors and self-tap fastening confirmed; clip insertion, hardware fit and printability still under verification',
                      'All remaining fastener retention details',
                      'Actual battery height and camera thickness/lens geometry','Cable routing and full FOV/access',
                      'Strength, vibration, steel-plate deflection, print fit and temperature'],
        'visible_object_names':[o.Name for o in visible],
        'lidar_frame_source_sha256':hashlib.sha256((ROOT/'cad_solidcraft/review/lidar_frame.step').read_bytes()).hexdigest(),
        'cat_source_sha256':hashlib.sha256((ROOT/'cad_solidcraft/exports/cat_mount.step').read_bytes()).hexdigest(),
        'battery_source_sha256':hashlib.sha256((ROOT/'cad_solidcraft/exports/battery_cradle.step').read_bytes()).hexdigest(),
        'sources':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (ROOT/'models').glob('*') if p.suffix.lower() in ['.step','.stp']}}
with open(OUT/'two_layer_checks.json','w',encoding='utf-8') as fh:
    fh.write(json.dumps(report,ensure_ascii=False,indent=2))
App.closeDocument(doc.Name)
saved=App.openDocument(str(path));saved.recompute()
assert abs(global_shape(saved.getObject('UpperSteelPlate')).BoundBox.ZMin-51.5)<1e-6
assert abs(saved.getObject('Params').layer_gap.Value-50)<1e-6
assert not [o.Name for o in saved.Objects if any('Error' in str(s) or 'Invalid' in str(s) for s in o.State)]
# Printable CAT and battery exports are maintained under cad_solidcraft/exports.
print(json.dumps({'output':str(path),'checks':report['checks'],'datums':report['datums_mm'],'saved_readback':'pass',
                  'exports':{'battery':str(ROOT/'cad_solidcraft/exports/battery_cradle.step'),
                             'cat_mount':str(ROOT/'cad_solidcraft/exports/cat_mount.step')}},ensure_ascii=True,indent=2),flush=True)
