"""Read-only inventory presentation; saves retain the original list of names."""
CATEGORIES = (("all", "全部"), ("medicine", "药物"), ("food", "食物"), ("important", "重要物品"))
ALIASES = {"项链": "奇怪的项链"}
ITEMS = {
    "帕尔的巧克力": dict(category="food", art=0, description="抓住小偷后收到的一份谢礼。", effect="效果待定义", verb="食用"),
    "药盒": dict(category="important", art=1, description="出院时医生交付的八槽旋转药盒。可从药盒入口选药，查看库存与推荐方案。"),
    "手机": dict(category="important", art=2, description="出院时从护士站取回的个人物品。"),
    "钱包": dict(category="important", art=3, description="装着证件和几张卡的钱包，出院时从护士站取回。"),
    "奇怪的项链": dict(category="important", art=4, description="若干哑黑的不规则几何体，由深褐色细麻线串起；受光处闪着碎银似的光泽。", source="出院时从护士站取回。"),
    "西铁月票": dict(category="important", art=5, description="阿弥替弗洛补办的公共交通月票。"),
    "地图": dict(category="important", art=6, description="精卫中心站工作人员提供的柏林市交通地图。"),
}

def canonical(item_id):
    return ALIASES.get(item_id, item_id)

def info(item_id):
    key = canonical(item_id)
    return dict(ITEMS.get(key, dict(category="important", art=None, description="资料待补。")), id=key, name=key)

def rows(inventory, category="all"):
    result = {}
    for item_id in inventory:
        item = info(item_id)
        if category != "all" and item["category"] != category:
            continue
        if item["id"] not in result:
            result[item["id"]] = dict(item, count=0)
        result[item["id"]]["count"] += 1
    return list(result.values())

def selected(rows, item_id=None):
    return next((item for item in rows if item["id"] == item_id), rows[0] if rows else None)

def use_blocked_reason(item):
    # No authored settlement exists. Never consume stock for a fake success.
    return "使用效果尚未定义" if item.get("verb") else "此物品没有可执行的使用操作"
