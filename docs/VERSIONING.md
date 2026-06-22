# ReMemorial 版本管理

## 唯一有效目录

- Ren'Py 开发项目：`E:\RenpyProject\ReMemorial`
- Git 仓库：`E:\Re-Memorial`
- `C:\Users\19512\Documents\ReMemorial` 是停用副本，不用于开发、提交或推送。

开发完成后，只把源代码、测试、文档和正式资源同步到 Git 仓库。不要同步
缓存、存档、编译文件、日志、错误报告、临时服务状态或构建产物。

## 分支

`main` 表示当前稳定的本地基线。较大的功能和修复应在短期分支完成：

- `feat/<name>`：新功能
- `fix/<name>`：修复
- `docs/<name>`：纯文档

合并前必须运行自动化测试和 Ren'Py lint。禁止改写已经共享或发布的
`main` 历史。

## 版本号

项目版本写在 `game/options.rpy`：

```renpy
define config.version = "0.0.0"
```

游戏内版本使用 `MAJOR.MINOR.PATCH`，Git 标签增加 `v` 前缀：

```text
游戏版本：0.0.0
Git 标签：v0.0.0
```

当前稳定基线是 `0.0.0`，下一次发布使用 `0.0.1`。进入明显的新开发阶段时
再提升到 `0.1.0`；正式完成版使用 `1.0.0`。

已发布标签不可移动、覆盖或重复使用。如果发布内容有问题，应修复后发布新的
补丁版本。

## 发布顺序

1. 同步并检查开发项目与 Git 仓库。
2. 运行完整自动化测试。
3. 运行 Ren'Py lint。
4. 更新 `config.version`。
5. 提交并推送 `main`。
6. 创建带说明的版本标签，例如 `v0.0.0`。
7. 推送标签并在 GitHub 创建同名 Release。

在步骤 2 和步骤 3 通过前，不得创建发布标签。
