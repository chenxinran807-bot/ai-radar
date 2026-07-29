# AI Radar

监控主流 AI 公司发布博客，kimi 自动大白话解读，推送飞书，生成静态站。

## 用法

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
export LARK_CHAT_ID=oc_xxx      # lark-cli 推送到群（bot 需在群里）
# 或 export LARK_WEBHOOK_URL=https://open.feishu.cn/open-apis/bot/v2/hook/xxx
.venv/bin/python main.py            # 跑一轮：抓取→解读→推送→建站
.venv/bin/python main.py --weekly   # 本周汇总
.venv/bin/python main.py --baseline # 首次/加新源后跑：存量文章标记 skipped 不推送
```

首次部署先跑 `--baseline` 再跑 `main.py`，否则历史文章会全部推送刷屏。

API 解读引擎（可选，OpenAI 兼容：火山方舟 / Moonshot 等）写进 `data/env`（已被 gitignore，不会入库）：

```bash
# data/env
AI_RADAR_API_KEY=你的key
AI_RADAR_API_BASE=https://ark.cn-beijing.volces.com/api/v3
AI_RADAR_API_MODEL=你的model-id或endpoint-id
# AI_RADAR_ALL_API=1   # 有这行则所有解读都走 API；没有则只有 importance≥4 的深度解读走 API
```

## 调度

```bash
mkdir -p data
cp com.airadar*.plist ~/Library/LaunchAgents/
launchctl load ~/Library/LaunchAgents/com.airadar.plist
launchctl load ~/Library/LaunchAgents/com.airadar.weekly.plist
```

## 结构

- `sources.yaml` 监控源（实测后定稿；纯 JS 渲染无法抓取的源见 git 历史）
- `prompt.md` 解读 prompt（核心资产）
- `fetch.py` / `interpret.py` / `push_lark.py` / `build_site.py` / `main.py`
