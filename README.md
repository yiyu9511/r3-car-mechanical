# R3 小车机械设计

当前采用两块相同的现有铁底板，层间铜柱暂按 **50 mm**：
第一层放前后 TOF、C30D MCU、电池；第二层放 CAT、雷达、相机。
保留铁板原轮廓和孔型，打印件只做设备转接和支撑。
C30D 实物为 V2.3，机械参考使用厂家 V2.2 STEP。

## 当前电池盒：M3×10+4 铜柱版

依据 `models/电池托架参考.step` 实测尺寸重建 SolidCraft 原生特征。
保留 62.6×86.6 mm 内腔、16 mm 出线口；去掉原安装耳，使用四根铜柱和嵌入式 M3 螺母。
两侧为一体功能边；底板整体 **4.4 mm**，中间两条扎带槽 **宽 6 mm、深 1.2 mm**，槽上剩余 **3.2 mm**。
本轮不做蜂窝或透气孔。

| 文件 | 用途 |
|---|---|
| [托架原生设计](cad_solidcraft/battery_cradle.sc) | 可编辑时间线，只有打印件 |
| [铜柱安装示意](cad_solidcraft/battery_mount.sc) | 托架 + 四铜柱 + 四螺母，五金为名义包络 |
| [STEP](cad_solidcraft/exports/battery_cradle.step) / [STL](cad_solidcraft/exports/battery_cradle.stl) | 当前几何导出，尚未完成打印与装车验收 |
| [托架预览](cad_solidcraft/renders/cradle_iso.png) / [底面](cad_solidcraft/renders/cradle_bottom.png) | 当前造型 |
| [安装近景](output/two_layer/battery_fit_closeup.png) | 电池盒、铜柱与底盘的实际几何位置，红色为后 TOF |
| [SolidCraft 底盘安装](cad_solidcraft/battery_on_chassis.sc) / [原生渲染](cad_solidcraft/renders/battery_on_chassis_render.png) | 在 SolidCraft 内直接查看电池盒、铜柱、螺母与原底盘 |
| [两层装配](assemblies/two_layer.FCStd) / [装配预览](output/two_layer/overview.png) | 已更新当前电池盒及铜柱 |
| [零件检查](cad_solidcraft/checks/battery_cradle_checks.json) / [装配碰撞检查](output/two_layer/collision_checks.json) | 几何证据与未解决事项 |

**已知装配问题：现有后 TOF 位置与电池盒底板干涉，尚未决定如何避让。**
不能将有效实体或导出成功理解为整车无干涉、可直接打印装车。
当前电池承托面 Z=15.9 mm；50 mm 层间高度下，预留 2 mm 后电池高度预算为 **33.6 mm**。
该预算尚不包含实际电池接头、线缆及完整装拆路径。

## 文档和后续任务

- [当前设计](docs/当前设计.md)：装配约束、定位与已知问题。
- [电池盒要求及测量](cad_solidcraft/电池托架需求存档.md)：最新用户要求与几何基准。
- [SolidCraft 重建与验证](cad_solidcraft/README.md)：入口、参数及命令。
- [C30D 安装说明](docs/C30D集成板安装说明.md)：板卡方向、铜柱与接线空间。
- [建模技能](.agents/skills/solidcraft-reference-modeling/SKILL.md)：参考取证、MCP 可见迭代、五金尺寸链、独立验收。

下一阶段先做 **打印件优化**，再做 **CAT 与底板的连接件**；具体清单见当前设计文档。
现有 CAT 连接件保留为装配基线，下一阶段重新审查，不作为已完成实物验证的成品。

## 目录与重建

- `models/`：适用组件源 STEP，不因日期较早而删除。
- `cad_solidcraft/`：当前电池盒、铜柱安装示意、生成与检查脚本。
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
