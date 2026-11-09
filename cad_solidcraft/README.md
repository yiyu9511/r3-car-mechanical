# SolidCraft 电池盒：当前铜柱版

2026-11-09，按用户最新反馈更新。源件是 `../models/电池托架参考.step`；
本目录 `exports/ref2_底盘主层板与电池底座.step` 与其哈希相同。
原配层板不用；原参考尺寸是依据，不沿用之前的打印柱/蜂窝版本。

## 当前几何与五金

| 项目 | 当前值 |
|---|---|
| 原托盘主体外廓 | 66.6×90.6 mm |
| 含功能边的打印件外廓 | 66.6×98×14.4 mm |
| 内腔两内壁间距 | 62.6×86.6 mm |
| 出线口 | 原件位置，宽 16 mm |
| 均匀底板 | 4.4 mm，局部 Z=-2.4..2 |
| 两条扎带槽 | X=-14..-8、8..14；宽 6，深 1.2，槽顶 Z=-1.2，槽上厚 3.2 |
| 功能边 | 两侧一体加强边，外角 2 mm 斜切，扎带出口完整切开 |
| 固定件 | M3×10+4 单头铜柱 ×4，外螺纹朝上；普通 M3 螺母 ×4 |
| 螺母窝 | 六角对边 5.8；螺母支承面 Z=-1；夹持底厚 1.4 |
| 螺柱通孔 | Ø3.3 |
| 名义五金 | 铜柱六角对边 5.5；螺母对边 5.5、高 2.4，待实物核对 |

螺柱尖低于电池承托面 0.4 mm，螺母顶低于承托面 0.6 mm，均为名义尺寸计算。
五金示意没有真实螺纹；铜柱内孔示意深度 6 mm 尚无厂家依据，不能据此选底部螺丝长度。
本轮没有蜂窝和透气孔，后续可评估简单直槽。

## 文件和状态

- `battery_cradle.sc`：打印件原生设计。
- `battery_mount.sc`：托架 + 四铜柱 + 四螺母，共 9 个实体。
- `battery_on_chassis.sc`：上述原生特征经刚体定位，插入原 R3 底盘；可在 SolidCraft 设计窗口旋转查看，不含其他设备。
- `renders/battery_on_chassis_render.png`：SolidCraft 自带 CPU 光线追踪，1400×1000；约 46 万三角面的原底盘使用 studio 资源配置。
- `checks/solidcraft_assembly_render.json`：软件实际完成的渲染任务及图片哈希。
- `exports/battery_cradle.step` / `.stl`：只导出打印件。
- `exports/battery_mount.step`：名义五金安装示意。
- `checks/battery_cradle_checks.json`：独立 OCCT 检查。
- `checks/solidcraft_inspect.json`：原生时间线及参数读数。
- `renders/`：当前零件与安装视图。

**零件几何符合本轮要求，整车装配仍有后 TOF 干涉。**
现有 TOF 实际表面与底板交叠面积约 301.5 mm²；包络重叠体积约 974.8 mm³。
两个读数采用不同方法，不是同一个测量量。后 TOF 未擅自移动。
打印配合、实际螺纹长度、材料、支撑、强度、温度、振动和电池实物尚未验证。

装配坐标：`X_world = y_local`，`Y_world = -x_local - 102.9`，`Z_world = z_local + 13.9`。
铜柱底面落在下层铁板顶面 Z=1.5；托架底面 Z=11.5、承托面 Z=15.9。
四锚点为 `(±43,-128.47)`、`(±39.04,-77.33)`；前锚点位于短长圆孔的端部圆弧中心。

## 重建

`solidcraft-cli` 从 PATH 或 `SOLIDCRAFT_CLI` 获取。GUI 内迭代使用：

```bash
solidcraft --control 27878
SOLIDCRAFT_CONNECT=127.0.0.1:27878 python3 cad_solidcraft/scripts/build_battery_cradle.py
```

生成器新建设计，默认输出到被忽略的 `cad_solidcraft/build/`；不会自动覆盖已接受的导出目录。
批处理设置 `SOLIDCRAFT_HEADLESS=1`，使用 `R3_CAD_OUT` 指定其他暂存目录。

```bash
SOLIDCRAFT_HEADLESS=1 python3 cad_solidcraft/scripts/build_battery_cradle.py
FREECAD_RUN="${FREECAD_RUN:-$HOME/.local/opt/freecad-1.1.4/squashfs-root/AppRun}"
"$FREECAD_RUN" python cad_solidcraft/scripts/verify_cradle.py
```

验证器检查生成目录的文件，并写出 STEP 读回、STL、装配坐标版本和报告。
它会因当前后 TOF 干涉返回非零；不要删除这项检查来获得“全通过”。
验证后按报告分辨零件与整车状态，再将本轮认可的结果替换到当前目录。

本机 Codex 与 DSH 已配置 SolidCraft MCP；DSH 为 `~/.dsh/profiles/web/cordis.patch.yml`。
跨机器不要照搬用户目录或 Windows 绝对路径。

## CAT 连接件：均匀厚板、内嵌螺母、四向直筋

用户已认可当前造型与软件装配效果；保留为后续打印试配基线，实物配合尚未验证。

- `cat_mount.sc`：当前打印件原生特征；`exports/cat_mount.step` / `.stl`：只含打印件。
- `cat_on_plate.sc`：CAT 原壳、连接件与上层铁板的 SolidCraft 场景；源壳几何未修改。
- `renders/cat_mount_underside.png` / `cat_rib_closeup.png` / `cat_assembled.png` / `cat_mount_on_plate.png`：当前视图。
- `checks/cat_mount_checks.json`：94 项几何检查通过；实物未验证项独立列出。
- `checks/cat_anchor_selection.json`：四个已确认孔的来源与测量；原选孔阶段壳底 Z66，当前加厚后为 Z68。

当前尺寸：托板 135.3256×98×5 mm，六个六角窝对边 5.8、从底面向上深 2.6，夹持层 2.4 mm。
四柱 Ø8×10，脚盘 Ø12×1.2，每柱四条 90°直筋，厚 2 mm，全高贯通，径向最远 5.8 mm。
底板使用 M3×10 自攻，导孔 Ø2.5×9 为试配值；外壳使用普通 M3×10＋普通 M3 螺母。
原外壳底板厚 2 mm；外壳＋整块托板叠厚 7 mm，但螺母嵌入后有效夹持厚度为 **4.4 mm**。
螺母按高 2.4 mm，螺纹穿出约 3.2 mm；须核对实际螺丝头和 PCB 内部净空。

坐标：打印件局部顶面 Z=0、底脚 Z=-15；总装平移 `[0,-50,68]`。
上层钢板 Z=51.5..53，CAT 底面 Z=68。导出仅反映几何，不代表完成打印或装车验收。
四孔已确认，不再把当前布局称为待选孔；旧选孔场景和中间斜筋样件已由当前装配替代。

```bash
"$FREECAD_RUN" python cad_solidcraft/scripts/prepare_cat_selection.py
SOLIDCRAFT_CONNECT=127.0.0.1:27878 python3 cad_solidcraft/scripts/build_cat_mount.py
"$FREECAD_RUN" python cad_solidcraft/scripts/verify_cat_mount.py
```

生成与检查默认写到 `cad_solidcraft/build/cat/`，是暂存目录。经检查后更新当前导出、文档与总装。
第一次准备脚本仍保留选孔命名，用途是提取原壳接口、完整外壳并复核已确认的四孔。
参数改变后需要重新验收；筋草图/固定结构不应只凭属性存在就宣称所有尺寸自动联动。
