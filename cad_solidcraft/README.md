# cad_solidcraft/ —— SolidCraft 工作流与电池托架

SolidCraft（solidcraft-cli 0.30.1）在本项目中的使用说明与交付件。
需求与全部确认过程见 [电池托架需求存档.md](电池托架需求存档.md)。

## 当前件：电池托架（v7，2026-11-09 用户确认）

| 文件 | 说明 |
|---|---|
| `battery_cradle.sc` | SolidCraft 原生设计（时间线可编辑） |
| `exports/battery_cradle.step` | 交付 STEP（单实体，66.6 × 90.6 × 12 mm，体积 18487 mm³） |
| `renders/cradle_v7_iso.png` / `_bottom.png` / `_top.png` | 渲染图 |
| `scripts/verify_cradle.py` | 数值验证（槽贯通/web/端壁窗口/法兰/柱孔） |
| `scripts/fix_step_solid.py` | STEP 导出成壳时用 OCCT 缝合修复 |

设计要点（建模顺序：盒 → 供电口 → 电池腔 → 扎带槽 → 四柱 → 法兰 → 导向孔 → 端部筋沿）：

- 基础盒 66.6 × 90.6 × 12（板 2 / 壁 2），电池腔顶开，左长壁 y -41..-23 供电口。
- **扎带槽 ×2**：中间两条纵向（x -63~-55、-43~-35），沿 Y 全程贯通；**从底部打薄 1.35 留 0.75 薄层（底板不切穿）**；
  只把两条槽 X 范围对应的**端壁切穿**（前后各 2 个窗口）。
- **四柱** Ø7×10 + **Ø14×3 圆形法兰**（接触面积约 154 mm²/柱），柱位对称：
  局部 (-23.73,±43)、(-74.87,±39.04) → 底盘孔 (±43,-128.47)、(±39.04,-77.33)。
  柱内 Ø2.5×7 自攻孔，M3×10 从下穿上、不碰主体。
- **端部筋沿**：两端各 3 段（跳过扎带窗口），覆盖后柱，作为功能性脚/加强沿。

装配变换：`x_world = y_local`、`y_world = -x_local - 152.2`、`z_world = z_local - 50`。

## 基础模型

| 文件 | 说明 |
|---|---|
| `exports/ref2_底盘主层板与电池底座.step` | 用户提供的原始参考件（含主层板 + 电池底座；主层板不属于本项目） |
| `exports/steel_plate.step` | 从 R3 底盘提取的 1.5 mm 钢板（上层板用） |
| `exports/LubanCat5_PCB_simplified.step` | 鲁班猫 5 PCB 简化板体（125×80×3.3，保留全部 14 个孔位） |
| `exports/LubanCat5_PCB_holes.txt` | 鲁班猫板 14 个孔位清单（x、y、直径 mm） |

## 工具

| 文件 | 说明 |
|---|---|
| `scripts/sc_mcp.py` | SolidCraft MCP stdio 客户端（`python scripts/sc_mcp.py reqs.json --wait 秒`） |
| `scripts/simplify_lubancat.py` | 鲁班猫板体提取导出（OCCT，`cadgen run`） |
| `scripts/bake_meshes2.py` / `bake_shell.py` | 供应商模型（C30D/雷达/CAT 壳）定位烘焙为 STL，供总装使用 |

## SolidCraft 使用要点

- CLI：`solidcraft-cli 0.30.1`（Windows 默认装在 `C:\Program Files\SolidCraft\`，本机放在 `E:\tools\SolidCraft-0.30.1\`，
  路径按本机安装调整）。
- MCP 注册在 `~/.dsh/profiles/desktop/cordis.patch.yml` 的 `solidcraft-mcp` 条目（stdio，`solidcraft-cli mcp`）；
  未重启 DSH 时用 `scripts/sc_mcp.py` 驱动。
- 桥接：GUI 打开时 MCP 自动桥到应用，建模实时可见；`--headless` 为独立会话。
- **每个 MCP 连接是独立设计会话**，相关操作须在同一次连接内完成；`file.insert_step` 等是引擎命令，走 `batch`/`execute`。

## 已知坑

- SolidCraft 0.30.1 的 STEP 导出偶发把实体写成壳：用 `scripts/fix_step_solid.py` 缝合修复，或按需改用 OCCT 导出。
- `selection.delete` 删实体：`items:[{"type":"body","name":"<名>"}]`，可先 dry_run。
- 拉伸 join 仅面贴合会被拒，需 0.1–0.2 mm 嵌入量；薄层短距切偶发静默失败，改用全高切。
- 选孔必须用实体探针（材料体积=0 才是通孔），别信旧清单/圆角面。
