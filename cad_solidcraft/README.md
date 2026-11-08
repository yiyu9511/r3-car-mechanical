# cad_solidcraft/ —— SolidCraft 工作流与基础模型

SolidCraft（solidcraft-cli 0.30.1）在本项目中的使用说明与基础模型归档。
**电池托架的 A1–A8 系列修改模型已全部删除**；需求与已核实数据见
[电池托架需求存档.md](电池托架需求存档.md)。

## 文件

| 文件 | 说明 |
|---|---|
| `电池托架需求存档.md` | **需求存档**：用户确认过的全部要求、已核实的底盘孔位/尺寸/装配变换、未定案项、过程教训 |
| `exports/ref2_底盘主层板与电池底座.step` | 用户提供的原始参考件（含主层板 + 电池底座两个实体；主层板不属于本项目） |
| `exports/steel_plate.step` | 从 R3 底盘提取的 1.5 mm 钢板（上层板用） |
| `exports/LubanCat5_PCB_simplified.step` | 鲁班猫 5 PCB 简化板体（125×80×3.3，保留全部 14 个安装/连接器孔位） |
| `exports/LubanCat5_PCB_holes.txt` | 鲁班猫板 14 个孔位清单（x、y、直径 mm） |
| `scripts/sc_mcp.py` | SolidCraft MCP stdio 客户端（`python scripts/sc_mcp.py reqs.json --wait 秒`） |
| `scripts/simplify_lubancat.py` | 鲁班猫板体提取导出（OCCT，`cadgen run`） |
| `scripts/bake_meshes2.py` / `bake_shell.py` | 供应商模型（C30D/雷达/CAT 壳）定位烘焙为 STL，供总装使用 |

## SolidCraft 使用要点

- CLI 安装：`E:\tools\SolidCraft-0.30.1\solidcraft-cli.exe`（Windows），`solidcraft-cli --version` 应为 0.30.1。
- MCP 注册：`~/.dsh/profiles/desktop/cordis.patch.yml` 中的 `solidcraft-mcp` 条目
  （stdio，`solidcraft-cli mcp`）；重启 DSH 后以原生 MCP 工具加载，未重启时用 `scripts/sc_mcp.py`。
- 桥接：GUI 打开时 MCP 自动桥到应用（默认 127.0.0.1:27878），建模实时可见；
  `--headless` 为独立会话。**每个 MCP 连接是独立设计会话**，相关操作须在同一次连接内完成。
- 命令走 `batch`/`execute` 工具（`file.insert_step` 等是引擎命令，不是 MCP 工具名）。

## 已知坑（详见需求存档第 5 节）

- STEP 导出会把圆柱面写成 BSpline，孔位敏感件用 `cadgen run`（build123d/OCCT）导出；
- `selection.delete` 删实体：`items:[{"type":"body","name":"<名>"}]`，可先 dry_run；
- 拉伸 join 仅面贴合会被拒，需 0.1–0.2 mm 嵌入量；薄层短距切偶发静默失败，改用全高切；
- 选孔必须用实体探针验证（材料体积=0 才是通孔），别信旧清单/圆角面。
