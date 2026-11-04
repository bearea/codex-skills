---
name: futou-bot
description: 在当前 Codex 会话中向飞书机器人“福头 ✨ 🤖”提问，并把机器人的答复带回当前会话。仅在用户明确要求向福头提问或调用本 Skill 时使用。
---

# 福头 ✨ 🤖

把用户写给福头的问题原样发到飞书私聊，等待机器人答复，并在当前 Codex 会话展示答复。不要自行回答该问题，也不要附带当前会话、文件或项目的其他内容。

## 首次使用

1. 确认已安装飞书官方 `lark-cli`。未安装时，引导用户按 [官方安装说明](https://github.com/larksuite/cli) 执行 `npx @larksuite/cli@latest install`；不要把机器人 App Secret 交给提问者。若尚未配置自己的飞书 CLI 应用，按官方 `lark-cli config init --new` 流程配置，再进行用户登录。
2. 运行 `python3 ~/.codex/skills/futou-bot/scripts/futou_chat.py doctor`（自定义 `CODEX_HOME` 时使用对应 Skill 路径）。它只检查 CLI、用户登录态、所需权限以及是否能核实与“福头 ✨ 🤖”的私聊，不发消息。若用户已在非默认 Lark CLI profile 登录，运行时设置 `FUTOU_LARK_PROFILE=<profile>`。
3. 若用户未登录或缺少权限，按 `doctor` 输出引导完成飞书用户身份授权。发送需 `im:message.send_as_user` 和 `im:message`；读取需 `im:message:readonly`（或飞书允许的等效消息权限），查找私聊需 `im:chat:read`。先核对当前应用是否已开通权限，再用 `lark-cli auth login --scope <缺少的权限> --no-wait --json` 发起用户授权；使用非默认 profile 时，授权命令也要加 `--profile`。按 `lark-shared` Skill 的授权流程展示链接与二维码；用户完成授权后再运行 `doctor`。不要使用机器人身份代替提问者发信。若自己的 CLI 应用无权开通某项权限，如实说明需要飞书应用管理员处理，不要切到机主的机器人应用身份绕过。
4. 若无法核实私聊，请用户先在飞书中与“福头 ✨ 🤖”完成一次问答，再重试 `doctor`。Skill 会核对机器人发信应用 ID，避免把同名机器人当成目标；不同 CLI 应用下的 `open_id` 可能不同，不用机主的 `open_id` 作通用定位。

## 提问

- 只有用户明确提供要发送的问题时才发送。调用本 Skill 并附上问题，已经明确了收件人、正文和以本人身份发送的意图；不要重复要求发送确认。
- 运行 `python3 ~/.codex/skills/futou-bot/scripts/futou_chat.py ask --text '<用户问题>'`。调用命令时安全引用用户原文，避免让引号、反引号或 `$()` 进入可执行的 Shell 表达式。脚本内部使用参数数组调用 `lark-cli`。
- 脚本输出 JSON：`status=answered` 时只把 `answer` 作为福头的答复展示，并可说明它来自飞书机器人；`status=timeout`、`ambiguous` 或报错时如实说明，不自行补写机器人答案。
- 答复需要机主审核时，机器人会先发“正在等待审核回复”。脚本会继续等待正式答复；超时则告知仍在等待，绝不把审核提示当最终答案。
- 当前桥接以新消息发回答案，尚未把答案作为原提问的飞书引用回复。脚本仅在此私聊没有其他新提问插入时自动配对；若发生并发或顺序不明，停止并提示去飞书核对，避免错配。

## 边界

- 该 Skill 是提问客户端。福头能读取什么、能做什么、何时审核，由机主 Mac 上的机器人和桥接控制。
- 不把 CLI 权限检查等同于飞书后台已批准的应用权限；以实际授权和发送结果为准。
- 此 Skill 不安装常驻服务，也不改动机主的桥接。
