# 烹饪实验室

本地浏览器试玩入口，与游戏内适配层共用 `game/systems/cooking_core`。食材目录在试玩中无限取用，用于验证配方；它不代表正式游戏的库存或经济。

在 PowerShell 中运行：

```powershell
& 'E:\renpy-8.5.3-sdk\lib\py3-windows-x86_64\python.exe' 'E:\RenpyProject\ReMemorial\standalone_cooking\server.py'
```

然后打开 [http://127.0.0.1:8765/](http://127.0.0.1:8765/)。也可使用已安装的 Python 3 运行 `server.py`。

等级、精力和骰型是试玩参数。每锅在按下“开始烹饪”时建立独立实例，随机结果写入本目录的 `.sessions.json`，浏览器刷新后可继续查看同一锅。清空后可开启新锅。

`WetGoopTarget`、扬州炒饭数值、食物效果以及技能树仍是策划待补配置。遇到依赖这些数值的分支，界面会显示待补状态。
