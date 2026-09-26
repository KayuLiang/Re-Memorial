# 烹饪核心数据

- `data/ingredients.json`：食材 Fixed、原始类别、degree 与 flavor load；果酱的 Fixed 由加工原料继承，因此表内为 `null`。
- `data/recipes.json`：138 道菜的 `required`、`limit`、`anti`、`Technique`、`R`、`Target`、`Budget`、优先级及覆盖配置。`当前推导`是可调整数据。
- `data/config.json`：规格、品质、XP、Flavor Matrix，以及明确待补的配置接口。

`required` 和 `limit` 使用通用条件，如 `米饭`、`water_degree==0`、`fruit>=1`、`oneof(鱼肉|鲜虾)` 与 `atleast3(鲜虾|蛋|meat|vegetable)`。运行时代码不按菜名分支。

修改 `R`、`Technique` 或规格后，可用 `formula_target`、`formula_budget` 重算该行的 `Target`、`Budget`。不要改动核心公式来调整单道菜。未定值保持 `null`，由调用方呈现 `configuration_pending`。

`rm_cooking.rpy` 是 Ren’Py 薄适配：维护食材库存、待结算锅、冻结随机、精力消耗、XP 增量和菜谱熟练度。采购、地图与正式餐次页面尚无已定数据来源，可通过该适配层的函数接入。
