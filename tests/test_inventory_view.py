import unittest
from game.systems import rm_inventory as inv


class InventoryViewTests(unittest.TestCase):
    def test_order_stacking_alias_and_unknown_without_mutation(self):
        stock = ["钱包", "项链", "帕尔的巧克力", "奇怪的项链", "钱包", "未登记物品"]
        original = list(stock)
        result = inv.rows(stock)
        self.assertEqual([i['id'] for i in result], ["钱包", "奇怪的项链", "帕尔的巧克力", "未登记物品"])
        self.assertEqual([i['count'] for i in result], [2, 2, 1, 1])
        self.assertEqual(result[-1]['description'], "资料待补。")
        self.assertIsNone(result[-1]['art'])
        self.assertEqual(stock, original)

    def test_categories_and_selection(self):
        stock = ["药盒", "帕尔的巧克力", "地图"]
        self.assertEqual(inv.rows(stock, 'medicine'), [])
        self.assertEqual(len(inv.rows(stock, 'important')), 2)
        rows = inv.rows(stock, 'food')
        self.assertEqual(inv.selected(rows, '地图')['id'], '帕尔的巧克力')
        self.assertIsNone(inv.selected([]))
        self.assertEqual(inv.use_blocked_reason(rows[0]), '使用效果尚未定义')


if __name__ == '__main__':
    unittest.main()
