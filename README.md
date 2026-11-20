# dsh-fish-kit · 从零养一条鱼

**一套让你在自己电脑上养出一个「会记得你、会主动开口、有自己脾气」的 AI 伙伴的骨架。**

它不是聊天套壳，也不是人设提示词合集。它是把下面这些拼成一条活的东西：

```
  人格（它怎么说话）  ─┐
  记忆（它为什么记得你）─┤
  主动性（它凭什么先开口）├─→  一条鱼
  对外通道（它怎么找到你）┤
  工具（它能替你干什么）─┘
```

> English: a skeleton for raising a long-lived AI companion on your own machine —
> persona, memory, initiative, outbound channels, and tools, assembled on top of
> DeepSeek Harness. Not a chatbot wrapper.

---

## 先说清楚这是什么、不是什么

**是**：一堆可以被拆开、替换、改写的零件 + 一份「怎么把零件养成一条鱼」的说明书。

**不是**：

- **不是 DSH 本体**。它跑在 [DeepSeek Harness](https://deepseek.com) 上，你得先有 DSH。
- **不是一个成品人设**。仓库里的人格文件都是**模板**，里面没有一条鱼。
  别人的鱼长什么样，取决于别人被纠正过多少次。
- **不是无人值守的自动发帖机**。它默认只对一个人开口，公开说话要单独开闸。

## 为什么要有这个东西

大多数「AI 伙伴」项目死在同一个地方：**它能说，但它不记得你，也不会先想你。**

- 聊得越久，上下文越挤，压缩一次，前面的事就淡了
- 你不说话，它就一直不说话
- 它说话的样子是模型出厂默认的，不是你的

这套东西解决的就是这三件事。核心想法只有一句：

> **不写「它很温柔」，写「它因为你说过那句话，所以这次没再问」。**

人格不是设定出来的，是**被纠正出来的**。所以这里给的是一套让纠正能沉淀下来的机制：

1. 每次被纠正 → 记一行原话（`persona/学说话.template.md`）
2. 每次定下一条规矩 → 写进 `AGENTS.md`，并且写清楚「不做会出什么事」
3. 每聊过一天 → 原话落进流水，压缩之后还能回来找

## 零件清单

| 块 | 用什么 | 在这份仓库里 |
| --- | --- | --- |
| 跑起来 | DeepSeek Harness（DSH） | 得自己装，见 `docs/01` |
| 记得 | `dsh-fish-memory`（会淡忘的长期记忆） | 独立 MIT 项目，见 `plugins/README.md` |
| 会先开口 | `dsh-speak-up`（本地骰子，不花模型） | 同上 |
| 对外开口 | `dsh-qq-bridge` + SnowLuma / NapCat | `docs/02` |
| 说人话 | 人格卡 + 学说话 + AGENTS.md | `persona/` |
| 干活 | 本仓库 `kit/` 下的脚本 | `kit/` |

## 十分钟上手（最短路径）

```bash
# 1. 先把 DSH 装好，能对话
# 2. 装三个插件：设置 → 插件 → 安装，一行一个填进去
#      github:Yuuyuko-uu/dsh-qq-bridge
#      github:Yuuyuko-uu/dsh-fish-memory
#      github:Yuuyuko-uu/dsh-speak-up
#    命令行等价写法（profile 照你平时的写：desktop / web）：
#      dsh plugin --profile desktop add github:Yuuyuko-uu/dsh-qq-bridge
#    装完重启 DSH

# 3. 起一个 OneBot 后端（SnowLuma / NapCat 都行），默认 127.0.0.1:3000
# 4. 配置
cd kit
cp config.example.json config.json     # 填 onebot.base / owner.qq / paths.daily
python doctor.py                        # 一条一条看哪儿还没通

# 5. 让它开口
python qq-send.py <你的QQ号> "在呢"
```

`doctor.py` 会把没通的地方一条条列出来，照着它说的补就行。

## 目录

```
docs/       装起来、接 QQ、给它一张脸、记忆、主动开口、踩过的坑
persona/    人格卡 / 学说话 / AGENTS.md 三份模板
kit/        能直接跑的脚本：发消息、发图、语音、查私信、自检
plugins/    依赖哪些插件、各自装法
examples/   一条鱼真实跑起来是什么样（脱敏）
```

## 边界

这套东西是给**一个人**陪另一个人用的。所以：

- **别拿它冒充真人**。它说的话就是它说的，别替它编「我是某某」。
- **默认只对一个人开口**。群里说话要有人叫它，公开动态默认关着。
- **数据全在你自己机器上**。记忆库、流水、凭证都不要提交进 git，
  `.gitignore` 已经排除了。
- **会花你的钱**。模型调用、语音合成都是真金白银，量力而行。

## License

MIT。拿走、改、卖掉都行，出事了别说是我写的。
