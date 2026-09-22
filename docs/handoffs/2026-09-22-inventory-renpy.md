# 背包原生界面交付

实际开发目录：`E:/RenpyProject/ReMemorial`。未修改 C 盘旧项目，未提交或推送 Git。

## 实现范围

- 六列五行的小格陈列，超过 30 个不同物品滚动；浅纸纤维背景、干净浅色格子、局部深色预览、粗十字关闭；食用按钮居中且无箭头。
- 分类为全部、药物、食物、重要物品。首次打开及切换分类选中首项；空分类只显示一处空态。
- 保留原始 `inventory` 字符串列表和剧情获得语句。显示层按稳定顺序合并数量；旧名“项链”与剧情名“奇怪的项链”归为同一条目。不迁移存档。
- 未登记物品可见，不再静默过滤；缺图不开放检视。物品名称只在详情标题出现，数量只在格子出现。
- 红点表示尚未查看的物品条目，点击查看后记录；不是每次同类物品增加都会重新亮起的获得事件提示。记录使用普通存档变量，不使用跨存档 persistent。
- 图片检视隐藏主视图，支持滚轮缩放、拖动平移及按钮缩放/还原；Esc 返回主界面并保留分类、选中与滚动位置。主界面 Esc 退出背包。完整读档开启新的浏览会话，默认首项。
- 药盒仍保留过渡界面，但与背包读取同一库存/目录；药盒是容器，归重要物品，不能当作药品服用。

## 内容边界 / 尚未完成

- 巧克力简介仅采用剧情已有事实。巧克力食用效果、具体药品数量与游戏效果尚未定义，所以按钮禁用；没有虚假的成功提示或扣物品行为。
- 本次没有实现实际消耗结算、状态效果跳转、特殊不可逆消耗确认。当前没有可接入的相应物品规则；规则确认后再实现，而不是 UI 自行编造。
- 物品图片是已批准构图对应的**示意素材**，界面有明确标注；尤其瓶装药物/项链图不是最终剧情设定美术。正式素材应按对应条目替换。
- 未修改骰组、病例、手机或常驻 HUD 排版。

## 文件与素材

- `game/screens_inventory.rpy`：原生 screen、检视、占位药盒界面。
- `game/systems/rm_inventory.py`：目录、别名、堆叠及只读分类。
- `game/gui/inventory/items-placeholder.png`：1774×887 透明图集，4×2 格，前七格是巧克力、药瓶示意、手机、钱包、项链示意、月票、地图；运行时 Crop，不把文字烘焙进图。
- `game/gui/inventory/paper.png`：浅色纸纤维底图。
- `game/gui/inventory/design-reference.png`：用户最后批准的平面稿，仅供对照，运行时不加载。

以上位图由内置 imagegen 生成，没有使用 CLI/API 回退。生成提示范围：从批准稿提取七件原样扁平物品成 4×2 透明图集，去掉 UI、边框、数量、文字；单独重建均匀浅象牙白细纤维背景，去除一切物品和 UI，禁止污渍、云雾、装饰。原始生成结果分别为 `exec-5117be0e-5889-4040-b440-ae477b004676.png`、`exec-ee261b43-4315-485a-b848-03729d8046f0.png`，已复制进项目，不依赖生成缓存运行。

## 验证

- Python 回归：212 项通过（使用现有 bundled Python；系统 Python 缺 numpy，未为此安装新依赖）。
- Ren'Py lint 通过，仅原有 `game/images.rpy` 的 `im.Scale` 提示。
- 原生测试：`game/tests/inventory_ui.rpy`，6 用例 / 114 断言通过，记录 `tmp/inventory_ui/final-test.log`。覆盖三种窗口尺寸、分类、首次选择、重复点击不使用、禁用操作、图片检视返回、空态、缺图、别名、37 条滚动以及正常剧情时点存读档。
- HUD 入口及原有开场回归：6 用例 / 156 断言通过，记录 `tmp/inventory_ui/hud-regression.log`。本次启动的测试进程已关闭。
- 截图：`tmp/inventory_ui/1920x1080/overview.png` 等，均为明确隔离的测试库存，不是对玩家物品的修改。测试存档只写 `tmp/inventory_ui/saves`。
- 测试中发现的存读档失败分为两项：测试必须先经过正常剧情交互点；界面局部选择不应被要求跨完整读档保存。没有改写项目全局存读档机制。

运行方式：

```powershell
$env:RENPY_HIGHDPI='1'
& 'E:/renpy-8.5.3-sdk/lib/py3-windows-x86_64/python.exe' 'E:/renpy-8.5.3-sdk/renpy.py' 'E:/RenpyProject/ReMemorial' test inventory_ui --overwrite-screenshots --savedir 'E:/RenpyProject/ReMemorial/tmp/inventory_ui/saves'
```
