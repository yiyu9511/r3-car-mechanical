# R3 小车机械设计

当前采用两块相同的现有铁底板，层间铜柱暂按 **50 mm**：
第一层放前后 TOF、C30D MCU、电池；第二层放 CAT、雷达、相机。
保留铁板原轮廓和孔型，打印件只做设备转接和支撑。
C30D 实物为 V2.3，机械参考使用厂家 V2.2 STEP。

## 当前电池盒：M3×10+4 铜柱版

依据 `models/电池托架参考.step` 实测尺寸重建 SolidCraft 原生特征。
保留 62.6×86.6 mm 内腔、16 mm 出线口；去掉原安装耳，使用四根铜柱和嵌入式 M3 螺母。
两侧为一体功能边；底板整体 **4.4 mm**，中间两条扎带槽 **宽 6 mm、深 1.2 mm**，槽上剩余 **3.2 mm**。
底板另开 4 条纵向圆头通槽（4×54 mm），避开扎带承托带和固定区；不做蜂窝。
外壁、上沿、槽口及外扩长边已做小圆角；靠端墙的两处螺母上方改为 8 mm 直边避让口，下面六角窝保留。

| 文件 | 用途 |
|---|---|
| [托架原生设计](cad_solidcraft/battery_cradle.sc) | 可编辑时间线，只有打印件 |
| [铜柱安装示意](cad_solidcraft/battery_mount.sc) | 托架 + 四铜柱 + 四螺母，五金为名义包络 |
| [STEP](cad_solidcraft/exports/battery_cradle.step) / [STL](cad_solidcraft/exports/battery_cradle.stl) | 当前几何导出，尚未完成打印与装车验收 |
| [托架预览](cad_solidcraft/renders/cradle_iso.png) / [底面](cad_solidcraft/renders/cradle_bottom.png) | 当前造型 |
| [安装近景](output/two_layer/battery_fit_closeup.png) | 电池盒、铜柱与底盘的实际几何位置，红色为后 TOF |
| [SolidCraft 底盘安装](cad_solidcraft/battery_on_chassis.sc) / [安装视图](cad_solidcraft/renders/battery_on_chassis.png) | 在 SolidCraft 内直接查看电池盒、铜柱、螺母与原底盘 |
| [两层装配](assemblies/two_layer.FCStd) / [装配预览](output/two_layer/overview.png) | 已更新当前电池盒及铜柱 |
| [零件检查](cad_solidcraft/checks/battery_cradle_checks.json) / [装配碰撞检查](output/two_layer/collision_checks.json) | 几何证据与未解决事项 |

**已知装配问题：现有后 TOF 位置与电池盒底板干涉，尚未决定如何避让。**
不能将有效实体或导出成功理解为整车无干涉、可直接打印装车。
当前电池承托面 Z=15.9 mm；50 mm 层间高度下，预留 2 mm 后电池高度预算为 **33.6 mm**。
该预算尚不包含实际电池接头、线缆及完整装拆路径。

## CAT 新连接件：四向直筋试配版

四个底板锚孔已由用户确认。当前采用 **135.33×98×5 mm 均匀托板**，保留原壳 8 槽与 6 孔，六个 M3 螺母窝嵌入底面。
四根 Ø8×10 mm 支撑柱，每柱四条 90°全高直筋（厚 2 mm），直筋收在 Ø12 柱脚轮廓内；脚盘背面新增连续 45°渐扩过渡，保持占地不变。
托板外角 R3、筋根 R0.6；底部外轮廓倒角 0.3，螺母窝和自攻孔入口倒角 0.25。与外壳贴合的上面轮廓保持原样。
外壳固定用普通 M3×10＋M3 螺母；底板固定用 M3×10 自攻螺丝，Ø2.5×9 导孔为试配值。

[原生打印件](cad_solidcraft/cat_mount.sc) · [SolidCraft 安装场景](cad_solidcraft/cat_on_plate.sc) ·
[底面效果](cad_solidcraft/renders/cat_mount_underside.png) · [柱筋近景](cad_solidcraft/renders/cat_rib_closeup.png) ·
[STEP](cad_solidcraft/exports/cat_mount.step) / [STL](cad_solidcraft/exports/cat_mount.stl) ·
[检查报告](cad_solidcraft/checks/cat_mount_checks.json)

CAT 底面因托板加厚升到 Z=68 mm；雷达扫描头最低包络高于 CAT 约 3.32 mm，已低于此前 5 mm 预留，视场仍需检查。
当前检查 211 项通过；STEP 重合实体布尔差有诊断警告，独立边界/体积读回一致。尚未完成实际免支撑打印、五金配合、PCB 下方螺丝头净空和装车验证。

## 文档和后续任务

电池架与 CAT 支架已由用户开始打印。当前新增[雷达与相机模块初稿](docs/雷达相机模块初稿.md)：
雷达安装耳和90°盲区朝后，四个已选锚孔固定，承托台下沿为前/左/右矩形孔带；相机为双挂钩座、俯仰小盒体和可拆后盖。
[SolidCraft 当前装配](cad_solidcraft/lidar_camera_system.sc) · [装配预览](cad_solidcraft/renders/lidar_camera_system.png)。
这是待完善初稿，不是打印发布件：相机厚度/孔径/镜头仍为暂估，下俯20°有干涉，主架导出有详细内核诊断警告。
[源接口分析](docs/雷达与相机接口分析.md)保留雷达实测与厂家图纸差异、相机确认尺寸。

[打印与配合基线](docs/打印与配合.md)：P2S、0.4 喷嘴、0.2 层高、4 道墙、顶底各 5 层、20% Gyroid；公差尚待 PLA/PETG 分别试配。

- [当前设计](docs/当前设计.md)：装配约束、定位与已知问题。
- [电池盒要求及测量](cad_solidcraft/电池托架需求存档.md)：最新用户要求与几何基准。
- [SolidCraft 重建与验证](cad_solidcraft/README.md)：入口、参数及命令。
- [C30D 安装说明](docs/C30D集成板安装说明.md)：板卡方向、铜柱与接线空间。
- [建模技能](.agents/skills/solidcraft-reference-modeling/SKILL.md)：参考取证、MCP 可见迭代、五金尺寸链、独立验收。

电池盒与 CAT 连接件都已有当前模型，后续做打印与五金试配优化，并解决已记录的装配问题；具体清单见当前设计文档。

## 目录与重建

- `models/`：适用组件源 STEP，不因日期较早而删除。
- `cad_solidcraft/`：电池盒、CAT件和当前雷达相机初稿；`exports/`是已有打印试配件，`review/`是新初稿检查STEP，勿混用。
- `assemblies/`：当前 C30D 基线及两层装配。
- `output/two_layer/`：当前装配检查与预览。
- `.agents/skills/`：本仓库的可复用建模技能。

FreeCAD 脚本使用安装包自带的 Python：

```bash
FREECAD_RUN="${FREECAD_RUN:-$HOME/.local/opt/freecad-1.1.4/squashfs-root/AppRun}"
"$FREECAD_RUN" python tools/build_two_layer_current.py
"$FREECAD_RUN" python tools/check_two_layer.py
xvfb-run -a "$FREECAD_RUN" freecad tools/render_current.FCMacro
```

`check_two_layer.py` 在已知干涉存在时返回非零，报告应保留失败项。
当前几何不是加工验收。仅在用户明确要求时提交或推送。
