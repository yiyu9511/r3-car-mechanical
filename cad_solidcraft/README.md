# SolidCraft 工作流说明（cad_solidcraft/）
本目录是电池托架 **A8** 的 SolidCraft 原生设计与导出件。所有路径相对本目录，换机器只需保证
`ref2_*.step`（或原版模型）与 SolidCraft CLI 可用。

## 文件

| 文件 | 说明 |
|---|---|
| `battery_cradle_a8.sc` | SolidCraft 原生设计（时间线可编辑） |
| `exports/battery_cradle_a8.step` | 交付 STEP（单实体，66.6 × 90.6 × 12 mm） |
| `exports/ref2_底盘主层板与电池底座.step` | 用户提供的原始参考件（仅作尺寸/开口参照，成品不含其层板） |
| `exports/steel_plate.step` | 从底盘提取的上层铁板（1.5 mm，另一层用） |
| `exports/LubanCat5_PCB_simplified.step` / `_holes.txt` | 鲁班猫 5 PCB 简化板体（保留全部 14 个孔位） |
| `renders/assembly_v11_view*.png` | 装在两层底盘上的效果图 |
| `scripts/sc_mcp.py` | MCP stdio 客户端（`python scripts/sc_mcp.py reqs.json --wait 秒`） |
| `scripts/verify_a8_final.py` | A8 数值验证（供电口/电池腔/槽/柱/web） |
| `scripts/fuse_a8.py` | 导出件多实体融合为单实体 |
| `scripts/simplify_lubancat.py` | 鲁班猫板体提取导出（OCCT） |
| `scripts/bake_meshes2.py` / `bake_shell.py` | 供应商模型定位烘焙 STL（总装用） |

## A8 设计要点

按用户指定顺序建模：基础盒 → 供电口 → 电池腔 → 四柱 → 扎带槽（最后）。

1. **基础盒** 66.6 × 90.6 × 12（z 61.5..73.5），地板 2 mm，四壁 2 mm。
2. **供电口**：左长壁 y -41..-23 全高窗口（照原始参考件位置）。
3. **电池腔**：x -80.6..-18、y -43.3..43.3，从 z 63.5 开顶。
4. **支撑柱**：4 × Ø7×10，柱底矩形法兰垫，柱内 Ø2.5×7 自攻孔（M3×10 从下穿上，
   螺丝尖距主体地板 ≥2.3 mm）。柱位对称：模型局部 (-23.73,±43)、(-74.87,±39.04)
   → 底盘孔 (±43,-128.47)、(±39.04,-77.33)，装配变换 `x=y_l, y=-x_l-152.2, z=z_l-50`。
5. **扎带槽（最后）**：两条纵向侧槽（平行长边），y -30..30，x 贴两侧（左 -82.7..-74.6、
   右 -24..-15.9），**侧壁完全切掉、底部只切薄留 0.8 mm web**（切薄不切空，扎带可绕外围
   一圈绑住电池）。槽 y 范围（≤30）与柱位（≥35.5）无重叠，柱下地板完整。

数值验证全部 PASS：单实体、供电口贯通、电池腔空、槽壁切穿 + web 保留、柱孔贯通、柱位地板完整。

## 已知经验

- SolidCraft 0.30.1 的 STEP 导出会把圆柱面写成 BSpline；孔位敏感件用 `cadgen run`（build123d/OCCT）导出。
- `selection.delete` 删实体：`items:[{"type":"body","name":"<名>"}]`，可先 dry_run。
- 拉伸 join 时若两体仅面贴合会被拒，留 0.1~0.2 mm 嵌入量。
- 薄层短距切（如 1.5 mm）偶发静默失败（changed_bodies 为空），改用大距离全高切更稳。
- MCP 每个连接是独立设计会话，全部操作须在同一次连接内完成；命令走 `batch`/`execute`。
- freecad 仓库 master 的 A2 方案已归档，当前件为本目录 A8（solidcraft 分支）。
