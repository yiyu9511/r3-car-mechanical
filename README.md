# R3 小车机械设计

> **分支说明**：本分支（`solidcraft`）用于 SolidCraft 工作流与基础模型归档。
> **电池托架的 A1–A8 系列修改模型已全部删除**；需求与已核实数据存档在
> [`cad_solidcraft/电池托架需求存档.md`](cad_solidcraft/电池托架需求存档.md)。
> FreeCAD 侧的 A2 方案同样归档，不再是当前件。分支切换：`git switch solidcraft` / `git switch master`。

当前电控为 **WHEELTEC C30D V2.3 驱控一体板**，使用厂家 V2.2 STEP 外形参考。
使用两块相同的现有铁底板搭两层，层间铜柱先按 **50 mm**（可调）。
第一层放 **前后 TOF、C30D MCU、电池**；第二层放 **CAT、雷达、相机**。
打印件只做设备与铁板之间的转接和支撑。

**两层架构、各层设备和 50 mm 层间高度已由用户确认。电池托架待按需求存档重新设计；
CAT 落脚锚孔仍用 FreeCAD 侧定案。**

## 电池托架：需求存档与基础模型（cad_solidcraft/）

- [电池托架需求存档](cad_solidcraft/电池托架需求存档.md)：用户确认的全部要求、
  已核实的底盘孔位/尺寸/装配变换、未定案项与过程教训。
- [原始参考件 STEP](cad_solidcraft/exports/ref2_底盘主层板与电池底座.step)
- [上层钢板 STEP](cad_solidcraft/exports/steel_plate.step)、
  [鲁班猫 PCB 简化 STEP](cad_solidcraft/exports/LubanCat5_PCB_simplified.step)

## 打印文件（output/two_layer/）

| 文件 | 说明 |
|---|---|
| [电池托架 STEP](output/two_layer/step/battery_cradle_a2.step) / [STL](output/two_layer/stl/battery_cradle_a2.stl) | A2 版：内腔/夹持/扎带槽保留，原 Ø3.4/26×105 封堵，改 M3 锚孔 (±50,-88.39)/(±50,-54.12)，前角小耳外扩 |
| [CAT 托板连接件 STEP](output/two_layer/step/cat_mount.step) / [STL](output/two_layer/stl/cat_mount.stl) | 贴壳托板（8 通风槽 + 6 固定孔）+ 四个 Ø13 带孔落脚，锚孔 (±50,-88.39)/(±50,-11.47)，孔 Ø3.0（M3，铁板 Ø3.2 补偿） |

## 从这里查看

| 文件 | 用途 |
|---|---|
| [当前设计](docs/当前设计.md) | 当前约束、两层布局、待解决事项 |
| [C30D 安装说明](docs/C30D集成板安装说明.md) | 板卡定位、铜柱高度、接线与维护空间 |
| [C30D 装配](assemblies/c30d_on_chassis.FCStd) | 按实际 6 mm 铜柱建立的参数化基线 |
| [当前两层装配](assemblies/two_layer.FCStd) | 同款铁板 ×2；包含上下层全部设备及打印转接件概念 |
| [两层预览](output/two_layer/overview.png) | 正常装配与分层查看 |
| [基线检查](output/current/baseline_checks.json) | 保存后复核、孔位误差、垫高与元件间隙 |
| [两层检查](output/two_layer/two_layer_checks.json) | 同板复制、层间高度、通风槽、设备净空及未验证项 |

## 目录

- `models/`：当前组件的源 STEP；电池参考包含原配层板和托架两个实体，原配层板不作为 R3 底板。
- `assemblies/`：当前已定位的装配基线。
- `output/two_layer/`：当前两层方案的预览与检查；不代表最终打印包。
- `docs/`：当前方案说明及仍适用的器件参考图。
- `tools/`：当前装配生成、检查和导入工具。

前后 TOF 和雷达已用厂家模型纳入布局；相机依据 IMX415 V1R1 尺寸图建立占位，板厚和镜头尺寸待实测。
电池只保留参考托架及高度预算框，尚无用户实际电池的完整几何。
过期装配、三件套转接件、旧电池模型、打印包、布局图和配套数据已从工作目录删除。

## 重新生成

FreeCAD 脚本需要 FreeCAD 自带的 Python 运行时（系统 `python3` 不能直接替代）。
下面的 `FREECAD_RUN` 指向本机 FreeCAD 安装目录里的 AppRun / freecadcmd，
**路径按本机实际安装位置设置**（便携版、squashfs 解包版或系统安装均可）：

```bash
FREECAD_RUN="${FREECAD_RUN:-$HOME/.local/opt/freecad-1.1.4/squashfs-root/AppRun}"   # 按本机修改
"$FREECAD_RUN" python tools/build_current_baseline.py
"$FREECAD_RUN" python tools/build_two_layer_current.py
"$FREECAD_RUN" python tools/check_two_layer.py
xvfb-run -a "$FREECAD_RUN" freecad tools/render_current.FCMacro   # 无显示环境才需要 xvfb-run
```

所有脚本都以仓库根目录为基准解析相对路径，仓库放在任意位置都能运行；
如需换位置，只改 `FREECAD_RUN` 指向的安装目录即可。

打开两层装配，在 `Params` 中修改 `layer_gap` 会联动上层板、上层设备、层间柱和电池高度预算。
CAT 连接件为贴壳托板 + 四个 Ø13 带孔落脚凸台，落脚坐于已确认锚孔 (±50,-88.39)/(±50,-11.47)，M3 对锁；
电池托架当前为 **SolidCraft A8**（solidcraft 分支 `cad_solidcraft/`），FreeCAD 侧 A2 已归档。
两块铁板均按源模型厚度 1.5 mm；上层底面 Z=51.5、顶面 Z=53 mm。

已安装 `freecad-scripts`、`freecad-imported-geometry-audit`、`freecad-model-validation` 三个技能，
分别用于脚本建模、导入几何检查和模型校验。
