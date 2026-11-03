# R3 小车机械设计

当前电控为 **WHEELTEC C30D V2.3 驱控一体板**，使用厂家 V2.2 STEP 外形参考。
使用两块相同的现有铁底板搭两层，层间铜柱先按 **50 mm**（可调）。
第一层放 **前后 TOF、C30D MCU、电池**；第二层放 **CAT、雷达、相机**。
打印件只做设备与铁板之间的转接和支撑。CAT 托板贴外壳底面并保留通风槽；电池托架沿用用户参考 STEP。

**两层架构、各层设备和 50 mm 层间高度已由用户确认。支脚、层间铜柱的实际可用孔及各设备锚孔尚未定案。**
孔位选择及禁用孔留到布局确认后讨论。当前没有可直接加工的最终打印包。

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

本机使用 FreeCAD 1.1.4 的 Python 运行时。系统 `python3` 用于普通脚本，不能直接替代 FreeCAD Python。

```bash
FREECAD_RUN="$HOME/.local/opt/freecad-1.1.4/squashfs-root/AppRun"
"$FREECAD_RUN" python tools/build_current_baseline.py
"$FREECAD_RUN" python tools/build_two_layer_current.py
"$FREECAD_RUN" python tools/check_two_layer.py
xvfb-run -a "$FREECAD_RUN" freecad tools/render_current.FCMacro
```

打开两层装配，在 `Params` 中修改 `layer_gap` 会联动上层板、上层设备、层间柱和电池高度预算。
CAT 连接件为贴壳托板与四个局部落脚；保留外壳原有 8 条通风槽和 6 个固定孔，尚未开铁板锚孔。
两块铁板均按源模型厚度 1.5 mm；上层底面 Z=51.5、顶面 Z=53 mm。电池承托面 Z=3.5 mm，留 2 mm 余量时电池高度上限为 46 mm。

已安装 `freecad-scripts`、`freecad-imported-geometry-audit`、`freecad-model-validation` 三个技能，
分别用于脚本建模、导入几何检查和模型校验。
