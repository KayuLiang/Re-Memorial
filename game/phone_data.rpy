# Shared phone state. Existing save variables remain authoritative.

default phone_calc_expr = ""
default phone_calc_result = "0"
default phone_draft_message = ""
default phone_chat_history = {}
default phone_story_ami_count = 0
default phone_story_ami_reply_ready = False
default phone_story_ami_sent = False
default phone_story_ami_active = False
default phone_read_counts = {}

init python:
    def phone_clock_text():
        minutes = store.current_time_minutes % (24 * 60)
        return "{:02d}:{:02d}".format(minutes // 60, minutes % 60)

    def phone_date_text():
        date, weekday, day, _, _ = rm_hud_clock_data()
        return "{}  {}".format(date or "第{}天".format(day), weekday).strip()

    def phone_received_count(contact_id):
        if contact_id == "ami":
            return 4 if store.phone_story_ami_sent else min(4, max(0, store.phone_story_ami_count))
        return sum(who != "我" for who, _ in store.phone_chat_history.get(contact_id, []))

    def phone_history(contact_id):
        # Both entry points project the same save state. Definitions are NOT history.
        lines = []
        if contact_id == "ami":
            lines = list(store.phone_chats["ami"][:phone_received_count("ami")])
            if store.phone_story_ami_sent:
                lines.append(("我", store.phone_story_ami_reply_text))
        return lines + list(store.phone_chat_history.get(contact_id, []))

    def phone_preview(contact_id):
        lines = phone_history(contact_id)
        return lines[-1][1] if lines else "暂无消息"

    def phone_unread(contact_id):
        received = phone_received_count(contact_id)
        # A legacy save's revealed messages have already been seen.
        return max(0, received - store.phone_read_counts.get(contact_id, received))

    def phone_mark_read(contact_id, adjustment):
        if adjustment.value >= adjustment.range - 8:
            count = phone_received_count(contact_id)
            if store.phone_read_counts.get(contact_id) != count:
                store.phone_read_counts[contact_id] = count
                renpy.restart_interaction()

    def phone_begin_story_ami():
        store.phone_story_ami_active = not store.phone_story_ami_sent
        if not store.phone_story_ami_sent and store.phone_story_ami_count == 0:
            store.phone_read_counts["ami"] = 0
            store.phone_story_ami_count = 1

    def phone_story_open_ami_chat():
        # Compatibility for existing callers; opening history never unlocks messages.
        pass

    def phone_can_reply(story_mode):
        return (story_mode and store.phone_story_ami_active
                and store.phone_story_ami_reply_ready and not store.phone_story_ami_sent
                and phone_received_count("ami") == 4)

    def phone_next_story_ami(expected_count):
        # Ignore a stale rapid click; each action reveals at most one authored line.
        if (store.phone_story_ami_active and not store.phone_story_ami_sent
                and store.phone_story_ami_count == expected_count and expected_count < 4):
            store.phone_story_ami_count += 1

    def phone_prepare_story_ami_reply():
        if not store.phone_story_ami_sent and phone_received_count("ami") == 4:
            store.phone_story_ami_active = True
            store.phone_draft_message = store.phone_story_ami_reply_text
            store.phone_story_ami_reply_ready = True

    def phone_send_story_ami_reply():
        if phone_can_reply(True):
            store.phone_story_ami_sent = True
            store.phone_story_ami_reply_ready = False
            store.phone_story_ami_active = False
            store.phone_draft_message = ""
            store.phone_read_counts["ami"] = 4

    def phone_calculate():
        expr = store.phone_calc_expr
        if not expr:
            store.phone_calc_result = "0"
            return
        if any(ch not in "0123456789+-*/(). " for ch in expr):
            store.phone_calc_result = "输入错误"
            return
        try:
            store.phone_calc_result = str(eval(expr, {"__builtins__": {}}, {}))
        except Exception:
            store.phone_calc_result = "计算错误"

define phone_story_ami_reply_text = "\u8c22\u8c22\u4f60\u7ed9\u6211\u9001\u7684\u8863\u670d\uff0c\u5f88\u5408\u8eab\u3002\u6211\u9a6c\u4e0a\u51fa\u6765\u4e86\u3002"

define phone_apps = [
    ("phone", "\u7535\u8bdd", "\u260e", "#34C759"),
    ("messages", "\u4fe1\u606f", "\u25cf", "#32D74B"),
    ("weather", "\u5929\u6c14", "\u2601", "#5AC8FA"),
    ("calendar", "\u65e5\u5386", "16", "#FF3B30"),
    ("notes", "\u7b14\u8bb0", "\u270e", "#FFD60A"),
    ("recorder", "\u5f55\u97f3\u673a", "\u25cf", "#FF453A"),
    ("clock", "\u65f6\u949f", "\u25f7", "#8E8E93"),
    ("album", "\u76f8\u518c", "\u25a7", "#AF52DE"),
    ("calculator", "\u8ba1\u7b97\u5668", "+", "#1C1C1E"),
]

define phone_contacts = [
    ("ami", "\u963f\u5f25", "\u51fa\u9662\u5feb\u4e50\uff01"),
    ("doctor", "\u533b\u751f", "\u590d\u8bca\u4fe1\u606f\u5360\u4f4d"),
    ("mom", "\u5988\u5988", "\u5185\u5bb9\u5360\u4f4d\uff0c\u5f85\u8865\u5145"),
    ("hospital", "\u533b\u9662\u516c\u4f17\u53f7", "\u533b\u7597\u62a5\u544a\u5360\u4f4d"),
]

define phone_chats = {
    "ami": [
        ("\u963f\u5f25", "\u5f17\u6d1b\uff0c\u6211\u628a\u4f60\u4e4b\u524d\u5f04\u810f\u7684\u8863\u670d\u90fd\u62ff\u56de\u53bb\u6d17\u4e86\u3002"),
        ("\u963f\u5f25", "\u65b0\u7684\u6362\u6d17\u8863\u670d\u4e5f\u8ba9\u62a4\u58eb\u5e2e\u5fd9\u5e26\u8fdb\u53bb\u4e86\uff0c\u4f60\u8bb0\u5f97\u627e\u5979\u62ff\u4e00\u4e0b\u3002"),
        ("\u963f\u5f25", "\u6536\u62fe\u597d\u4e1c\u897f\u5c31\u51fa\u6765\u627e\u6211\u5427\uff0c\u6211\u5728\u4e2d\u5fc3\u7684\u5927\u5385\u7b49\u4f60\uff01"),
        ("\u963f\u5f25", "\u4e24\u4e2a\u6708\u6ca1\u89c1\u4e86\uff0c\u6211\u5bf9\u4f60\u53ef\u662f\u53c8\u62c5\u5fc3\u53c8\u60f3\u7684\uff0c\u8fd8\u4e0d\u5feb\u70b9\u51fa\u6765\u8ba9\u6211\u62b1\u4e00\u4e0b\u3002"),
        ("\u6211", "\u8c22\u8c22\u4f60\u7ed9\u6211\u9001\u7684\u8863\u670d\uff0c\u5f88\u5408\u8eab\u3002\u6211\u9a6c\u4e0a\u51fa\u6765\u4e86\u3002"),
    ],
    "doctor": [("\u533b\u751f", "\u5185\u5bb9\u5360\u4f4d\uff1a\u590d\u8bca\u65f6\u95f4\u548c\u533b\u7597\u62a5\u544a\u5c1a\u672a\u5b9e\u88c5\u3002")],
    "mom": [("\u5988\u5988", "\u5185\u5bb9\u5360\u4f4d\uff1a\u5bb6\u5ead\u76f8\u5173\u5bf9\u8bdd\u5c1a\u672a\u5b9e\u88c5\u3002")],
    "hospital": [("\u533b\u9662\u516c\u4f17\u53f7", "\u5185\u5bb9\u5360\u4f4d\uff1a\u533b\u9662\u901a\u77e5\u5c1a\u672a\u5b9e\u88c5\u3002")],
}

