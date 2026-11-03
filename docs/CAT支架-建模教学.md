# CAT（鲁班猫5）支架 · FreeCAD 参数化建模教学

> 对应成品：`freecad/cat_bracket.FCStd`（由 `tools/cat_bracket.py` 生成，可打开对照）
> 结构：3mm 底板紧贴小车底盘（8 锚孔）+ 2 条跑道形肋排（17mm）撑起 CAT，总垫高 20mm，免铜柱
> 锚孔配圆形沉孔（φ6.5 深 2.5）埋 M3 螺母；CAT = M3×10 自攻进肋顶盲孔，免长螺丝免螺母
> 锚孔：底盘实测 M3 孔 10 点 (±60,27.61)(±60,11.61)(±20,29.35)(±50,-11.46)(±44,-35.97)
> CAT：外壳下主体 6 孔（2列×3行，实测 (-25.86/29.14)×(7.5/0/-7.5)）；中心 φ20 走线孔对位底板大孔

本教学与脚本 `tools/cat_bracket.py` 一一对应，GUI 手做一遍即可掌握全部要点。

---

## 第 1 步：建参数表（Spreadsheet）

1. 切到 **Spreadsheet 工作台** → 工具栏「新建电子表格」→ 左侧树里按 F2 重命名为 `Params`。
2. 按下表填写（A 列名称、B 列数值、C 列备注）：

| 单元格 | 输入内容 | 别名 | 含义 |
|---|---|---|---|
| B2 | `=20 mm` | `lift_total` | 总垫高（底板上表面→CAT 底面）|
| B3 | `=3 mm` | `plate_thk` | 顶板厚度 |
| B4 | `=1.5 mm` | `z_base` | 底板上表面高度 |
| B5 | `=135 mm` | `plate_dx` | 顶板长 |
| B6 | `=85 mm` | `plate_dy` | 顶板宽 |
| B7 | `=-7 mm` | `plate_cy` | 顶板中心 Y |
| B8 | `=3 mm` | `corner_r` | 圆角 |
| B9 | `=3.4 mm` | `hole_m3` | M3 通孔（打印补偿 +0.4）|
| B10 | `=10 mm` | `post_d` | 立柱外径 |
| B11 | `=20 mm` | `center_d` | 中心走线孔 |
| B12 | `=2.5 mm` | `pilot_d` | 肋顶 M3 自攻底孔（盲孔）|
| B13 | `=10 mm` | `pilot_dep` | 自攻底孔深（不到底板）|
| B14 | `=6.5 mm` | `nut_cb_d` | 锚孔圆形沉孔径（螺母对角 6.35+间隙）|
| B15 | `=2.0 mm` | `nut_cb_dep` | 锚孔沉孔深（留 1.0mm 承压 web）|
| B16 | `=-25.86 mm` | `catx1` | CAT 孔位 左列 X（下主体实测）|
| B17 | `=29.14 mm` | `catx2` | CAT 孔位 右列 X（两列不对称）|
| B18 | `=7.5 mm` | `catya` | CAT 孔位 行1 Y |
| B19 | `=0 mm` | `catyb` | CAT 孔位 行2 Y |
| B20 | `=-7.5 mm` | `catyc` | CAT 孔位 行3 Y |
| B21 | `=60 mm` | `ax1` | 锚孔1 ±X |
| B22 | `=27.61 mm` | `ay1` | 锚孔1 Y 前外 |
| B23 | `=60 mm` | `ax2` | 锚孔2 ±X |
| B24 | `=11.61 mm` | `ay2` | 锚孔2 Y 前内 |
| B25 | `=20 mm` | `ax3` | 锚孔3 ±X |
| B26 | `=29.35 mm` | `ay3` | 锚孔3 Y 前中 |
| B27 | `=50 mm` | `ax4` | 锚孔4 ±X |
| B28 | `=-11.46 mm` | `ay4` | 锚孔4 Y 后部 |
| B29 | `=44 mm` | `ax5` | 锚孔5 ±X |
| B30 | `=-35.97 mm` | `ay5` | 锚孔5 Y 车尾（底盘实测对称对）|
| B31 | `=lift_total - plate_thk` | `post_h` | 立柱高（派生）|

3. **设别名**：点中 B2 → 右键 → 「别名…」→ 输入 `lift_total` → 确定。逐个设置。
   - 别名规则：字母开头、无空格无中文。
4. **★大坑（实测踩过）**：带负号的值直接输 `-8 mm` 会被当成**纯文本**，表达式求值报
   `Cannot convert str to Quantity`，且错误只在控制台出现、模型静默不更新。
   **所有数值统一写成 `=数值 mm` 的公式形式**（等号开头），强制按带单位数量解析。

## 第 2 步：新建 Body 与底板草图

1. 切到 **PartDesign 工作台** → 「创建实体」(Body) → 改名 `CAT_Bracket`。
2. 选中 Body → 「新建草图」→ 选 **XY 平面**。
3. 草图高度绑定：关闭草图编辑，左侧选中草图 → 下方属性面板 `Placement → Position → z`
   → 点输入框右侧 **fx 圆形图标**（表达式编辑器）→ 输入（**底板贴底盘**）：
   ```
   Params.z_base
   ```
4. 双击进入草图，画矩形（4 条线 + 4 个重合约束 + 2 水平 2 竖直）。
5. 加 4 个尺寸约束（X/Y 距离），**每个都在输入框右侧点 fx 绑表达式**：

| 约束 | 表达式 |
|---|---|
| 左下角 X | `-Params.plate_dx / 2` |
| 左下角 Y | `Params.plate_cy - Params.plate_dy / 2` |
| 右上角 X | `Params.plate_dx / 2` |
| 右上角 Y | `Params.plate_cy + Params.plate_dy / 2` |

   约束全部生效后草图变绿（全约束）。

## 第 3 步：底板拉伸 + 圆角

1. 选中草图 → 「凸台」(Pad) → Length 点 fx 绑 `Params.plate_thk` → OK。
2. 按住 Ctrl 选 4 条竖直边 → 「圆角」(Fillet) → Radius 点 fx 绑 `Params.corner_r`。

## 第 4 步：跑道形肋排（2 条，撑起 CAT）

每条肋 = 1 矩形 + 2 圆帽，共 3 草图 3 个 Pad（顺序融合即成跑道形）：
1. **矩形草图** `Sketch_肋排N`：Placement.z 绑 `Params.z_base + Params.plate_thk / 2`，
   四边距离约束绑 `Params.catx1/2 ± Params.post_d / 2`（X 向）、
   `Params.catyc` / `Params.catya`（Y 向）。Pad Length 绑 `Params.post_h + Params.plate_thk / 2`。
2. **圆帽草图** `Sketch_帽N_行1`：圆心绑 (`catx1/2`, `Params.catya`)，直径绑 `Params.post_d`，同样 Pad。
3. **圆帽草图** `Sketch_帽N_行3`：圆心 Y 改 `Params.catyc`，其余同上。

> ★为什么不画"两弧两线"的完整跑道草图：FreeCAD 1.1 求解器对「双弧 + 多约束」不稳定
> （Equal/双半径约束直接 Invalid）；矩形+圆帽三 Pad 融合效果相同且稳。

## 第 4.5 步：锚孔圆形沉孔（10 个，板上表面）

1. 新建草图，Placement.z 绑 `Params.z_base + Params.plate_thk`（**板顶面**）。
2. 画 10 个圆：圆心同锚孔（`±Params.ax1~5` / `Params.ay1~5`），直径绑 `Params.nut_cb_d`。
3. Pocket → Length 绑 `Params.nut_cb_dep`（**不勾 ThroughAll**，向下 2.5mm）。
   效果：M3 螺母埋进板面不晃、不凸出。圆形即可，不必六角。

## 第 5 步：孔组（两张草图，两个 Pocket）

**A. 底板孔组（11 孔）**：
1. 新建草图，Placement.z 绑 `Params.z_base + Params.plate_thk`（板顶面）。
2. 画 10 个锚孔（圆心绑 `±Params.ax1~5` / `Params.ay1~5`，直径绑 `Params.hole_m3`）
   + 1 个中心走线孔（圆心 0,0，直径绑 `Params.center_d`）。
3. Pocket → Type **ThroughAll**。

**B. CAT 固定孔（6 个肋顶自攻盲孔）**：
1. 新建草图，Placement.z 绑 `Params.z_base + Params.plate_thk + Params.post_h`（肋顶面）。
2. 画 6 个圆：圆心同肋排孔位（`catx1/catx2` × `catya/yb/yc`），直径绑 `Params.pilot_d`。
3. Pocket → **不勾 ThroughAll**，Length 绑 `Params.pilot_dep`（10mm 盲孔，不到底板）。
   装配：M3×10 从外壳内侧下拧，自攻进肋排 6~8mm，**不需要长螺丝和螺母**。

## 第 6 步：验证参数化

打开 Params 表：
- `lift_total` 改 `=25 mm` → 立柱变高 5mm（柱顶 21.5→26.5）
- `hole_m3` 改 `=3.6 mm` → 10 个锚孔一起变大；`hole_cat` 单独控 6 个 CAT 孔

改完按 `Ctrl+R` 重算，确认无误后改回。

## 第 7 步：导出

选中 Body → 文件 → 导出 → STL（网格偏差 0.1mm）/ STEP。
脚本已自动导出 `output/cat_bracket.stl` 与 `output/cat_bracket.step`。
**打印前铁律：先打 1:1 纸样贴底盘比对 8 个锚孔**（见 `freecad/docs/装配路线图.md` 阶段4）。
打印方向：底板朝下平放、立柱朝上，无需支撑。

---

## 常见坑速查

| 症状 | 原因 | 解法 |
|---|---|---|
| 改参数模型不动、无报错 | 负数单元格被存成文本 | 单元格改写成 `=-8 mm` |
| 表达式里找不到参数表 | 用了中文 Label | 用内部名 `Params.xxx` 或 `<<中文名>>.xxx` |
| 约束报"冗余" | 重合/水平约束加重复 | 删多余约束，保持草图全约束（绿色）|
| Pad/Pocket 方向反了 | 法向判断 | 勾 Reversed，或把草图放对侧平面 |
| 表达式输不进去 | 没点 fx 图标 | 每个可输入框右侧的圆形 fx 按钮才是表达式入口 |
