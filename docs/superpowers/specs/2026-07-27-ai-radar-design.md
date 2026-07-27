# AI Radar 设计文档

日期：2026-07-27
状态：已确认（待 spec 复审）

## 1. 定位与形态

一个**本地定时管道**（pipeline，非 agent），监控全球主流 AI 公司的模型发布博客，自动生成**面向非技术读者**的大白话解读，推送到飞书，并生成一个可选公开的静态网站。

受众：第一版只给自己用；架构预留小圈子扩展口（公开静态页 + 飞书群），不做用户系统。

核心差异化：解读质量与推送时机。解读 prompt（`prompt.md`）是项目核心资产，独立成文件、随时可迭代。

## 2. 整体架构

```
launchd 定时（每天 08:00 / 20:00）→ main.py
  → fetch.py      抓取 + 去重 → data/radar.db (SQLite)
  → interpret.py  kimi CLI / API 生成解读
  → push_lark.py  飞书卡片推送
  → build_site.py 生成静态 HTML → data/site/
```

原则：单源失败不阻塞其他源；解读失败标记待重试，下次运行补跑；飞书推送失败重试 3 次后记日志放弃。

## 3. 数据源（sources.yaml）

每源一条 YAML 记录：名称、URL、抓取方式（rss / scrape）、解析规则、关键词过滤器。加源 = 加配置，不改代码。

**RSS/Atom 直接订阅**：OpenAI、Anthropic、Google DeepMind、Mistral、Cohere、Moonshot、智谱、阿里 Qwen

**轻量 scraper**（无稳定 RSS）：Meta AI、xAI、DeepSeek、字节 Seed/豆包、阶跃星辰、MiniMax、百度文心

去重与降噪：
- URL + 标题哈希去重，存 SQLite
- 关键词粗筛（release / introducing / 发布 / 开源 等）→ 解读阶段模型二次判断"是否模型发布相关"，否则丢弃不推送

## 4. 解读引擎（prompt.md + interpret.py）

固定四段结构，约 300–400 字：

1. **一句话**：这事是什么；禁术语，必须用时当场大白话解释
2. **对你有什么用**：分三种读者——普通用户 / 开发者（API 价格能力）/ 行业关注者（相对竞品的强弱）
3. **和别家比**：一句话定位（如"能力与 Claude X 相当，价格一半"）
4. **原文链接** + 可信度标记（官方公告 / 第三方爆料）

双引擎混合：
- 日常：本机 kimi CLI（零额外费用）
- 重大发布：Moonshot API 深度解读。importance 由第一遍解读输出 `importance: 1-5`，≥4 触发深度版

后续演进：深度解读环节可升级为 agent（自主查资料、对比历史发布）；管道内单环节替换，不动整体架构。

## 5. 推送与调度（push_lark.py）

- 飞书机器人交互卡片：标题（公司+内容）、importance 星级、四段正文、"查看原文"按钮
- importance ≥4 红色标题栏，普通蓝色
- 新文章即时逐篇推送，不攒批
- 单源一次抓出多篇（发布会连发）→ 合并为一张卡片，防刷屏
- 每周日一条"本周汇总"卡片：按公司分组 + "本周最值得关注的 X"

调度：launchd，每天 08:00 与 20:00 各跑一次（覆盖美东/国内发布时段）。

## 6. 静态站（build_site.py）

纯 HTML，零依赖、无构建工具：Python 脚本 + 单个 HTML 模板直接渲染。

- 首页：解读卡片按时间倒序（飞书卡片内容的网页版）
- 顶栏按公司筛选
- `archive/` 按月归档

自己用阶段本地打开即可；公开 = push 到 GitHub Pages。

## 7. 项目结构

```
ai-radar/
├── sources.yaml      # 监控源配置
├── prompt.md         # 解读 prompt（核心资产）
├── fetch.py          # 抓取 + 去重
├── interpret.py      # kimi CLI / API 解读
├── push_lark.py      # 飞书卡片推送
├── build_site.py     # 静态 HTML 生成
├── main.py           # 管道入口，launchd 调用
├── docs/             # 设计文档
└── data/             # SQLite (radar.db) + site/
```

## 8. 明确不做（YAGNI）

- 用户系统、订阅管理、多推送渠道（Telegram/邮件）
- arXiv / HuggingFace trending 等噪音源
- Web 框架、数据库服务、前端构建链
- Agent 化的全流程（仅保留深度解读环节的升级可能）
