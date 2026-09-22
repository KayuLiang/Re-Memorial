# ReMemorial 开场 UI 工作交接报告

更新时间：2026-06-20  
用途：供下一次 Codex 会话直接继续修改“开始游戏后的系统确认第一幕”UI。

## 1. 项目位置与硬性规则

- 唯一活跃 Ren'Py 项目：`E:\RenpyProject\ReMemorial`
- 唯一本地 Git 备份仓库：`E:\Re-Memorial`
- 不要从 `C:\Users\19512\Documents\ReMemorial` 读取、修改、提交或推送项目。
- 修改完成后先运行 Ren'Py lint，再将源码和资源同步至 `E:\Re-Memorial`。
- 备份时排除：`cache`、`saves`、`*.rpyc`、`*.rpymc`、`*.pyc`、日志、错误和 traceback。

## 2. 用户已经确认的设计方向

目标是高质量的 lofi 仿 Win7 医院系统官网界面，混合以下气质：

- 千禧年早期网页与经典 Win7 窗口
- 梦核、医院终端、电子示波器
- 低饱和莫兰迪绿色，避免鲜艳荧光绿
- 蓝色经典窗口边框，四边必须统一
- 边框比普通 UI 粗约 1.5～2 倍，可带轻微粗糙像素感
- 浏览器/系统窗口之外的区域更暗，突出主体
- 视觉应扁平化，避免写实、廉价或过度渐变
- CRT 噪点存在，但不能破坏文字可读性

用户此前已经确认当前整体方向“对了”。继续修改时应以局部精修为主，不要推翻现有视觉语言。

当前核心色值：

```renpy
opening_color_desktop = "#6f8078"
opening_color_desktop_dark = "#46534f"
opening_color_border = "#5b8db8"
opening_color_border_dark = "#315f88"
opening_color_paper = "#e7e4d9"
opening_color_phosphor = "#a8c7aa"
```

## 3. 已实现的剧情和交互

开场 Scene00～Scene14 已完整实现：

1. 系统免责声明和开始确认。
2. 水滴、闪回和医院环境声音占位。
3. Win7 医疗系统桌面启动。
4. 医疗档案加载、状态更新和通知。
5. 六节完整知情同意书。
6. 同意书必须完成 viewport 首次测量并滚动到底，才能点击“下一页”。
7. 身份和属性确认。
8. 属性为真实可分配数据：
   - 体质固定为 3。
   - 力量、敏捷、智力、意志初始均为 1。
   - 额外可分配 17 点。
   - 单项最低 1，最高 20。
   - 必须分完 17 点才能签署。
9. 签署需要鼠标在签署区域内连续按住 1.5 秒。
10. Scene14 只有黑底数字 `3 / 2 / 1`，没有最后几张 CG。
11. 倒计时前显式停止 `sound` 和 `opening_foley`，之后硬静音 2.5 秒。
12. 最终跳转到原剧情 `mountain_memory_start`。

## 4. UI 当前结构

主要实现文件：

- `game/screens_opening_system.rpy`
  - Win7 医疗系统桌面、窗口、任务栏和所有医疗页面。
  - 同意书、身份确认、属性分配、签署、倒计时。
  - 大部分下一轮 UI 修改应集中在此文件。
- `game/crt_effect.rpy`
  - `subtle`、`interference`、`shutdown` 三档 CRT。
- `game/opening_sequence.rpy`
  - Scene00～14 的流程、音效调用和页面切换。
- `game/opening_stats.rpy`
  - Ren'Py store 层的属性默认值和包装函数。
- `game/opening_stats_logic.py`
  - 独立、可测试的属性分配规则。
- `game/script.rpy`
  - `start` 跳入完整新开场；旧剧情从 `mountain_memory_start` 继续。
- `game/images/effects/crt_*.png`
  - CRT 扫描线与三张噪点纹理。

`screens_opening_system.rpy` 中适合直接调整的区域：

- 68 行附近：`opening_system_desktop`
- 136 行附近：`opening_window_frame`
- 287～455 行：桌面、窗口、标题栏、正文、任务栏样式
- 603～749 行：加载、档案、通知、验证、倒计时页面
- 752～858 行：同意书预览和完整文档
- 859～1120 行：身份、属性和签署
- 1182～1479 行：各业务页面的具体 style

当前窗口正文启用了裁切，避免内容再次越过底部边框。浏览器四边边框已经统一，任务栏顶部只保留一条细高光线。

## 5. 已完成的视觉修正

- 浏览器底边已与其余三边统一，不再把边框画进内容。
- 内容已限制在窗口内部。
- 任务栏上边框已减细并对齐。
- 主窗口外区域已经压暗。
- 绿色改为低饱和莫兰迪方向。
- 同意书滚动条改为低饱和医疗配色。
- 身份页面内容已收进窗口边界。
- 签署区域高度已压缩。
- 示波器波形改为代码绘制，不再使用可能缺字的字符。
- 文档遮盖块已统一使用 `rememorial_ui_font`，主字体为汇文明朝体，缺字回退到思源黑体。
- 已用 1920×1080 实际截图检查过 loading、records、consent、identity、verification 页面。

## 6. 不应破坏的逻辑

修改 UI 时必须保留以下行为：

- `opening_system_desktop` 的主窗口正文裁切。
- 主窗口四边统一粗蓝框。
- 同意书 `Adjustment.ranged` 首次测量门槛；不能仅用默认 `range=1` 判断到底。
- 同意书必须真实滚动到底。
- 体质固定 3；其余四项使用 17 点池，范围 1～20。
- 未分完点数时不能签署。
- 签署必须根据 `renpy.get_game_runtime()` 计算真实 1.5 秒。
- mouseup 时需重新检查持续时间，不能只依赖 0.05 秒 timer。
- Scene14 不得加入 CG，只能显示数字。
- 开场期间 inventory、phone、quick menu 等普通游戏 UI 必须隐藏。
- 音频资源缺失时保持静默回退，不能因缺文件崩溃。

## 7. 测试与验证

当前自动化测试：

```powershell
py -m unittest discover -s tools -p 'test_opening_*.py' -v
```

最近结果：`99/99` 通过。

Ren'Py lint：

```powershell
& 'E:\renpy-8.5.3-sdk\renpy.exe' 'E:\RenpyProject\ReMemorial' lint
```

最近结果：退出码 `0`，无错误输出。

测试文件：

- `tools/test_opening_contracts.py`
- `tools/test_opening_stats.py`

若修改尺寸、边框、任务栏、同意书、属性页或签署区域，应同步更新或补充视觉契约测试，而不是直接删除失败断言。

## 8. Git 与备份状态

本地备份仓库当前提交：

```text
a81c4e8 chore: complete local project backup
```

上一个功能修复提交：

```text
e27cff7 fix: harden opening consent and delivery
```

当前状态：

- `E:\Re-Memorial` 工作树干净。
- 本地 `main` 比 `origin/main` 领先 1 个提交。
- 远端仍停留在 `e27cff7`。
- `a81c4e8` 已完整补入 GUI、字体、背景、角色图和项目基础文件。
- 2026-06-20 最后一次尝试时，本机无法连接 `github.com:443`，因此推送失败。

网络恢复后执行：

```powershell
git -C E:\Re-Memorial push origin main
```

## 9. 当前已知限制

- `game/audio/opening/` 目前主要是文件命名说明，缺少正式音效时会静默播放。
- 当前活跃项目中会因 Ren'Py 运行产生 `cache`、`saves`、`*.rpyc` 等文件；这些属于正常运行生成物，不要同步到 Git。
- 旧的 localhost 端口不应视为固定地址。下一会话需要重新启动项目后，再使用 in-app browser 检查当前端口。
- 目前没有需要修复的 Critical 或 Important 代码审查问题。

## 10. 下一会话建议工作方式

下一会话可直接使用以下任务说明：

> 请阅读 `E:\RenpyProject\ReMemorial\docs\handoffs\2026-06-20-opening-ui-work-report.md`，继续精修开场 Win7 医疗系统 UI。只使用活跃项目 `E:\RenpyProject\ReMemorial`，备份仓库为 `E:\Re-Memorial`。先启动并在 1920×1080 下截图检查当前页面，再根据我的反馈修改 `game/screens_opening_system.rpy`。保留同意书滚动门槛、属性分配和 1.5 秒签署逻辑，不要加入倒计时 CG。修改后运行 99 项测试与 Ren'Py lint，再同步、提交和推送。

建议优先检查顺序：

1. 主窗口四边框、正文裁切、底边和任务栏衔接。
2. 同意书长文本的字号、行距、留白和滚动条。
3. 身份/属性页面的信息密度与签署区域比例。
4. CRT 噪点强度和文字可读性。
5. 1920×1080 实机截图中的对齐和溢出。
