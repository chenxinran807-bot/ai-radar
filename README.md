# AI Radar

监控主流 AI 公司发布博客，kimi 自动大白话解读，推送飞书，生成静态站。

## 用法

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
export LARK_WEBHOOK_URL=https://open.feishu.cn/open-apis/bot/v2/hook/xxx
export MOONSHOT_API_KEY=sk-xxx   # 可选，importance≥4 深度解读用
.venv/bin/python main.py          # 跑一轮：抓取→解读→推送→建站
.venv/bin/python main.py --weekly # 本周汇总
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
