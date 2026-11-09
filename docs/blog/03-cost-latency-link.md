# 03 · 成本与延迟为什么必须画在同一张图

## 当时我怎么看这个问题

单独看 latency dashboard，你会去砍工具超时；单独看账单，你会去换小模型。但真实回归往往是：**某条慢 span 既贵又慢**（大上下文重复塞入），或**又便宜又慢**（队列/重试/冷启动）。拆开看会开错药方——我亲自干过：把模型降级后，p95 更差了，因为小模型不会用缓存路径，反而多次重试。

另一次，月度 cost 暴涨，APM 却显示「平均延迟还行」。拆开 span 才发现是少数 `llm.chat` 的 `tokens_in` 从 800 漂到 6k，平均值被大量短请求稀释。

## 试过什么

1. **两套表**：FinOps 一张，APM 一张。对齐 request id 全靠人，周会吵架。
2. **只在月末看 cost**：来不及跟某次版本变更关联，优化窗口已过。
3. **只报 token 平均数**：被极端长 prompt 淹没，也看不出是哪个工具链导致的。
4. **只盯成功请求**：失败重试的费用消失在「错误率」里，账单却实打实扣了。

## 为什么否决

否决「成本与延迟分家」。同一条 span 上必须同时留 `duration_ms`、`tokens_in/out`、`cost_usd`，summary 才能排出「$/s」与「贵且慢」的元凶。也否决「只在网关总账看钱」——要能下钻到 `retrieve` / `llm.chat` / `tool.*` 名字层。

## 最终怎么解

- 写 span 时带 usage（`tracer.record_usage`）
- demo 单价在 `pricing.py`，本地估算，不依赖账单 API
- `summary.py` 聚合：每 name 的 p50/max 延迟、token、cost；全局 total_cost
- CLI：`python -m obs_lab.cli summary --trace out/demo.jsonl`

实践里我会再加一个「贵且慢」过滤器：`duration_ms` 高于阈值且 `cost_usd` 高于阈值的 span name，优先进优化 backlog。

## 用到的具体 skill / 技巧清单

| Skill | 用法 |
|-------|------|
| **cost 挂 span** | `record_usage` + `pricing.estimate_cost` |
| **按 name 聚合** | `summary.aggregate` |
| **找贵且慢** | 过滤高 duration × 高 cost |
| **与路由联动** | attrs.route = cheap|strong |
| **与缓存联动** | attrs.cache = hit|miss（姊妹仓） |
| **JSONL 可 diff** | 改版本前后各跑 demo，比 total_cost |

## 代码解析（按文件路径）

### `lab/src/obs_lab/pricing.py`

演示用每千 token 单价。生产应换成你们真实价目或账单导出；接口保持 `estimate_cost(model, in, out)` 即可。

### `lab/src/obs_lab/summary.py`

`load_spans` → `aggregate`。刻意用 JSON 打印，方便管道进 notebook 或另存基线。

### `lab/src/obs_lab/cli.py`

`demo` 造一条含两次 `llm.chat`（small/large）的 trace，`summary` 立刻能看出 large 对 cost 的贡献。

把 tracing 做成「能讲清楚一次请求为什么又贵又慢」的素材，而不是又一份没人看的日志——这是本仓和纯 APM 教程的差别。
