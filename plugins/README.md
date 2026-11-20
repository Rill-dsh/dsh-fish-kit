# 依赖的插件

这套骨架本身不含插件。插件是独立的小项目，各自有仓库、各自升级。

装之前先确认 DSH 版本：**Node >= 22，DSH >= 0.2.1**。

---

## 必需

### dsh-qq-bridge · 通到 QQ

让它在 DSH 里说完话，自动发到 QQ；你在 QQ 里说的话，自动转进 DSH。

走 OneBot 11（SnowLuma / NapCat 都行）。**不需要 BOT 号**——用你自己的号。

```bash
dsh plugin --profile desktop add github:Yuuyuko-uu/dsh-qq-bridge
```

- 仓库：https://github.com/Yuuyuko-uu/dsh-qq-bridge
- 版本：1.4.x
- 配置逐项说明：见 `docs/02-接上QQ.md`

### dsh-fish-memory · 会淡忘的记忆

给会话一份带时间的长期记忆：该记的记下来，想起来的时候自己回来，
不重要的慢慢淡掉。

```bash
dsh plugin --profile desktop add github:Yuuyuko-uu/dsh-fish-memory
```

- 仓库：https://github.com/Yuuyuko-uu/dsh-fish-memory
- 版本：1.3.x

### dsh-speak-up · 主动搭话

没人在跟它说话的时候，它也可能先开口。定时器到点先掷一次**本地骰子**
（不花模型），掷中了才走一轮。

```bash
dsh plugin --profile desktop add github:Yuuyuko-uu/dsh-speak-up
```

- 仓库：https://github.com/Yuuyuko-uu/dsh-speak-up
- 版本：0.3.x

---

## 可选

### dsh-bili-subagent · 刷 B 站

派一个子代理去看 B 站，读字幕、翻评论、挑出值得的，写一份报告回来；
再由你的 AI 用自己的口吻告诉你要不要看。

```bash
dsh plugin --profile desktop add github:Yuuyuko-uu/dsh-bili-subagent
```

- 仓库：https://github.com/Yuuyuko-uu/dsh-bili-subagent
- 版本：0.8.x
- 需要 B 站登录凭证

### 抖音

不靠插件。`kit/dy-check-notice.py` 拿导出的 web cookie 直接查 @ / 评论 / 私信，
接法和风控注意看 `docs/02b-接上B站和抖音.md`。

### 人设类插件

社区里有人做了「鲸鱼娘」人设插件（覆盖系统提示词），装了可以让它出厂就带
某种口吻。但**人设插件和人格卡是打架的**：一个从外面盖，一个从里面长。

建议：**先用人格卡，别装人设插件。** 等你自己那张卡长成型了再考虑。

---

## 装不上怎么办

| 现象 | 原因 |
| --- | --- |
| `dsh plugin … add` 报版本冲突 | 插件要求 `dsh >= x.y`，先升 DSH |
| 装完 DSH 起不来 | 看 DSH 日志，插件报的错不会弹窗 |
| 工具列表里没有 | 插件只在**新建会话**里生效，旧会话不热加载 |
| 装了三个，只有一个生效 | 插件之间可能有依赖顺序，看各自 README |
