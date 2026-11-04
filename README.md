# Codex Skills

可独立安装的 Codex Skills 集合。每个 Skill 位于 `skills/<名称>/`，后续可以继续在 `skills/` 下添加其他 Skill。

## 已收录

| Skill | 用途 |
| --- | --- |
| [福头 ✨ 🤖](skills/futou-bot/SKILL.md) (`futou-bot`) | 在自己的 Codex 会话里向福头飞书机器人提问，并等待正式答复 |

## 安装福头 ✨ 🤖

在安装了 Codex 的电脑上，使用内置 Skill Installer：

```bash
python3 ~/.codex/skills/.system/skill-installer/scripts/install-skill-from-github.py \
  --repo bearea/codex-skills --path skills/futou-bot
```

也可以先克隆本仓库，再把 `skills/futou-bot` 复制到自己的 `${CODEX_HOME:-$HOME/.codex}/skills/`。安装后新开 Codex 会话，选择“福头 ✨ 🤖”或输入 `$futou-bot 你的问题`。

### 使用前准备

1. 安装[飞书官方 Lark CLI](https://github.com/larksuite/cli)，配置自己的 CLI 应用并以自己的飞书用户身份登录。此 Skill 不需要、也不应获取福头机器人的 App Secret。
2. CLI 应用及用户授权需允许读取私聊、以用户身份发送消息：`im:chat:read`、`im:message`、`im:message:readonly` 和 `im:message.send_as_user`。若已授权，可直接继续；若缺少，Skill 会提示补齐。应用后台开通权限和用户本人授权是两步。
3. 在飞书中先与“福头 ✨ 🤖”完成一次问答，以便核实机器人身份。机器人是否对你可见由飞书应用的可用范围控制。
4. 运行只读检查：

   ```bash
   python3 ~/.codex/skills/futou-bot/scripts/futou_chat.py doctor
   ```

如果 Lark CLI 的授权不在默认 profile，可在运行检查和提问时设置 `FUTOU_LARK_PROFILE=<profile>`。

机器人收到问题后的处理、资料访问与答复审核由[主机侧桥接工程](https://github.com/bearea/feishu-codex-desktop-bridge)负责；本仓库中的 Skill 只代表安装者发送问题、等待并显示答复。当前桥接把答复作为新消息发送，Skill 遇到同一私聊中的并发提问会停止自动配对，提示回飞书核对。其他用户的跨机器安装与授权仍需实际验证。

## 开发

每个 Skill 自带 `SKILL.md`、可选的 `agents/openai.yaml` 和必要的脚本。不要提交飞书凭证、访问令牌或个人聊天记录。

## 许可

MIT，见 [LICENSE](LICENSE)。
