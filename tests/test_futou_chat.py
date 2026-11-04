import importlib.util
import unittest
from pathlib import Path
from unittest.mock import patch


SCRIPT = Path(__file__).resolve().parents[1] / "skills/futou-bot/scripts/futou_chat.py"
spec = importlib.util.spec_from_file_location("futou_chat", SCRIPT)
futou = importlib.util.module_from_spec(spec)
spec.loader.exec_module(futou)


def bot_message(message_id, content):
    return {"message_id": message_id, "content": content,
            "sender": {"sender_type": "app", "id": futou.BOT_APP_ID}}


class FutouChatTests(unittest.TestCase):
    def test_resolves_chat_by_app_even_when_bot_open_id_differs(self):
        chats = [{"name": futou.BOT_NAME, "p2p_target_type": "bot",
                  "p2p_target_id": "ou_different_for_another_app", "chat_id": "oc_right"},
                 {"name": futou.BOT_NAME, "p2p_target_type": "bot",
                  "p2p_target_id": "ou_lookalike", "chat_id": "oc_wrong"}]
        with patch.object(futou, "cli", return_value={"data": {"chats": chats}}), \
             patch.object(futou, "messages", side_effect=lambda chat: [bot_message("om_a", "答复")] if chat == "oc_right" else []):
            self.assertEqual(futou.find_chat(), "oc_right")

    def test_waits_past_review_notice_for_final_answer(self):
        old = bot_message("om_old", "旧答复")
        sent = {"message_id": "om_sent", "content": "问题", "sender": {"sender_type": "user"}}
        waiting = bot_message("om_wait", futou.REVIEW_NOTICE)
        answer = bot_message("om_answer", "正式答复")
        with patch.object(futou, "cli", return_value={"data": {"message_id": "om_sent"}}), \
             patch.object(futou, "messages", side_effect=[[old], [waiting, sent, old], [answer, waiting, sent, old]]), \
             patch.object(futou.time, "sleep"), \
             patch.object(futou, "emit") as emit:
            futou.ask("问题", 10, "oc_chat")
        self.assertEqual(emit.call_args.args[0], "answered")
        self.assertEqual(emit.call_args.kwargs["answer"], "正式答复")

    def test_refuses_to_pair_reply_after_another_user_question(self):
        old = bot_message("om_old", "旧答复")
        sent = {"message_id": "om_sent", "content": "问题", "sender": {"sender_type": "user"}}
        other = {"message_id": "om_other", "content": "另一题", "sender": {"sender_type": "user"}}
        answer = bot_message("om_answer", "无法确认归属")
        with patch.object(futou, "cli", return_value={"data": {"message_id": "om_sent"}}), \
             patch.object(futou, "messages", side_effect=[[old], [answer, other, sent, old]]), \
             patch.object(futou, "emit") as emit:
            futou.ask("问题", 10, "oc_chat")
        self.assertEqual(emit.call_args.args[0], "ambiguous")


if __name__ == "__main__":
    unittest.main()
