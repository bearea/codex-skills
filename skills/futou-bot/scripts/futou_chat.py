#!/usr/bin/env python3
"""Ask the owner's Feishu bot through the official lark-cli as the current user."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
import uuid


BOT_NAME = "福头 ✨ 🤖"
BOT_APP_ID = "cli_aa63800ff7791c2c"
REVIEW_NOTICE = "正在等待审核回复，审核完成后会继续答复。"
REQUIRED_SCOPES = {"im:chat:read", "im:message", "im:message.send_as_user"}
READ_SCOPES = {"im:message:readonly", "im:message.p2p_msg:get_as_user"}


def emit(status: str, **details: object) -> None:
    print(json.dumps({"status": status, **details}, ensure_ascii=False))


def cli(*args: str) -> dict:
    env = os.environ.copy()
    env["LARKSUITE_CLI_NO_UPDATE_NOTIFIER"] = "1"
    env["LARKSUITE_CLI_NO_SKILLS_NOTIFIER"] = "1"
    profile = os.environ.get("FUTOU_LARK_PROFILE")
    command = ["lark-cli", *(["--profile", profile] if profile else []), *args, "--json"]
    result = subprocess.run(command, capture_output=True,
                            text=True, env=env, timeout=45)
    raw = result.stdout if result.returncode == 0 else result.stderr
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"飞书 CLI 返回无法解析的结果（退出码 {result.returncode}）") from exc
    if result.returncode or payload.get("ok") is False:
        error = payload.get("error") or {}
        raise RuntimeError("飞书 CLI 调用失败：" + str(error.get("message") or "未知错误")
                           + "; missing_scopes=" + str(error.get("missing_scopes") or [])
                           + "; hint=" + str(error.get("hint") or ""))
    return payload


def check_auth() -> None:
    status = cli("auth", "status", "--verify")
    user = status.get("identities", {}).get("user", {})
    if user.get("status") != "ready" or user.get("verified") is False:
        raise RuntimeError("飞书用户身份未就绪。请先按 lark-shared Skill 完成 lark-cli 用户授权。")
    scopes = set(str(user.get("scope") or "").split())
    missing = sorted(REQUIRED_SCOPES - scopes)
    if not scopes.intersection(READ_SCOPES):
        missing.append("im:message:readonly")
    if missing:
        raise RuntimeError("缺少飞书用户授权：" + ", ".join(missing)
                           + "。请确认当前 CLI 应用已开通这些权限，再逐项运行 "
                           + "lark-cli auth login --scope <权限> --no-wait --json 并完成授权。")


def find_chat() -> str:
    result = cli("im", "+chat-list", "--as", "user", "--types", "p2p",
                 "--sort", "active_time", "--page-size", "100", "--page-all",
                 "--page-limit", "20")
    candidates = [c for c in result.get("data", {}).get("chats", [])
                  if c.get("p2p_target_type") == "bot" and c.get("name") == BOT_NAME]
    verified = []
    for chat in candidates:
        chat_id = chat.get("chat_id")
        if isinstance(chat_id, str) and chat_id.startswith("oc_"):
            if any(bot_message(item) for item in messages(chat_id)):
                verified.append(chat_id)
    if len(verified) != 1:
        raise RuntimeError(f"未能核实与 {BOT_NAME} 的唯一飞书私聊。请先在飞书与机器人完成一次问答，再重试。")
    return verified[0]


def messages(chat_id: str) -> list[dict]:
    result = cli("im", "+chat-messages-list", "--as", "user", "--chat-id", chat_id,
                 "--order", "desc", "--page-size", "50", "--page-all",
                 "--page-limit", "2", "--no-reactions")
    return result.get("data", {}).get("messages", [])


def bot_message(item: dict) -> bool:
    sender = item.get("sender") or {}
    return sender.get("sender_type") == "app" and sender.get("id") == BOT_APP_ID


def pending_question(items: list[dict]) -> bool:
    for item in items:
        if item.get("deleted"):
            continue
        if bot_message(item):
            if (item.get("content") or "").strip() == REVIEW_NOTICE:
                return True
            return False
        if (item.get("sender") or {}).get("sender_type") == "user":
            return True
    return False


def after_sent(items: list[dict], sent_id: str) -> list[dict] | None:
    for index, item in enumerate(items):
        if item.get("message_id") == sent_id:
            return list(reversed(items[:index]))
    return None


def ask(question: str, timeout_seconds: int, chat_id: str) -> None:
    if not question.strip():
        raise RuntimeError("请提供要发给福头的问题")
    if pending_question(messages(chat_id)):
        raise RuntimeError("此私聊已有尚未答复的问题。请等待其完成后再通过 Skill 提问，以免混淆答复。")
    sent = cli("im", "+messages-send", "--as", "user", "--chat-id", chat_id,
               "--text", question, "--idempotency-key", "futou-" + uuid.uuid4().hex)
    sent_id = sent.get("data", {}).get("message_id")
    if not isinstance(sent_id, str) or not sent_id.startswith("om_"):
        raise RuntimeError("消息可能已发出，但飞书没有返回消息 ID；请在飞书中核对，避免重复发送")
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        recent = after_sent(messages(chat_id), sent_id)
        if recent is None:
            emit("ambiguous", message="找不到刚发出的消息，无法安全匹配答复，请在飞书私聊中核对",
                 sent_message_id=sent_id)
            return
        for item in recent:
            if item.get("deleted"):
                continue
            if (item.get("sender") or {}).get("sender_type") == "user":
                emit("ambiguous", message="等待期间此私聊出现另一条用户消息，无法确定答复对应哪一题",
                     sent_message_id=sent_id)
                return
            if not bot_message(item):
                continue
            answer = item.get("content") or ""
            if not isinstance(answer, str):
                continue
            if answer.strip() == REVIEW_NOTICE or answer.strip().startswith("福头 ✨ 已收到你在云文档中的提问，正在等待审核回复"):
                continue
            if answer.strip():
                emit("answered", answer=answer, sent_message_id=sent_id,
                     answer_message_id=item.get("message_id"))
                return
        time.sleep(6)
    emit("timeout", message="福头尚未返回正式答复，可能仍在处理或等待机主审核；请稍后在飞书私聊中查看",
         sent_message_id=sent_id)


def main() -> int:
    parser = argparse.ArgumentParser(description="在 Codex 中向飞书机器人福头 ✨ 🤖 提问")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("doctor", help="只读检查飞书 CLI、授权和机器人私聊")
    ask_parser = sub.add_parser("ask", help="发问并等待答复")
    ask_parser.add_argument("--text", required=True, help="要原样发送的问题")
    ask_parser.add_argument("--timeout", type=int, default=600, help="等待秒数，默认 600")
    args = parser.parse_args()
    try:
        if not shutil.which("lark-cli"):
            raise RuntimeError("未安装飞书官方 lark-cli。安装说明：https://github.com/larksuite/cli")
        check_auth()
        chat_id = find_chat()
        if args.command == "doctor":
            emit("ready", bot=BOT_NAME, chat_id=chat_id,
                 message="用户登录态、所需权限及机器人私聊已找到；尚未发送测试消息")
        else:
            if not 10 <= args.timeout <= 1800:
                raise RuntimeError("--timeout 必须介于 10 到 1800 秒")
            ask(args.text, args.timeout, chat_id)
        return 0
    except (RuntimeError, subprocess.TimeoutExpired) as exc:
        emit("error", message=str(exc))
        return 1


if __name__ == "__main__":
    sys.exit(main())
