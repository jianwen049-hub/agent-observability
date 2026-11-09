# 01 · Traces / Spans：把 Agent 从黑盒拉出来

## 当时我怎么看这个问题

Agent 一接上工具，故障形态就变了：用户说「答得慢而且错」，你却只看得到最终一句回复。是检索慢？模型 TTFT 高？工具超时重试了三次？还是 prompt 拼太大触发了排队？没有 span，这些全是猜。

我早期的做法是 `print` 时间戳——很快变成几千行噪声，而且跨工具调用对不上同一个 request id。更糟的是，异常栈只指向业务代码，看不出是「第几次工具调用」炸的。

## 试过什么

1. **到处打 log**：缺结构化，无法聚合 p95，更无法按 trace 重建时间线。
2. **直接上完整 OpenTelemetry + 远端 collector**：正确但重。本地实验、单机脚本、博客 demos 被基础设施绑死，离线都跑不起来。
3. **只用托管平台**：好用，但隐私与成本敏感场景需要「先有本地真相」，再决定是否外送。
4. **仅在网关打一条总耗时**：知道慢，不知道谁慢。

## 为什么否决

否决「没有 parent/child 的散装日志」。否决「demo 也强依赖外部 collector」。可观测性的**数据模型**应先于厂商 SDK：trace_id、span_id、parent_span_id、name、attrs、start/end、status。有了这个模型，再映射到 OTel / 托管平台是适配问题，而不是推倒重来。

## 最终怎么解

本仓实现一个**进程内 JSONL tracer**（`lab/src/obs_lab/tracer.py`）：

- 一次用户请求 = 一条 `trace`
- 模型调用、工具调用、检索 = child `span`
- 落盘为 JSONL，一行一个完成态 span（含 duration_ms）
- 用 `contextvars` 传递当前 span，避免把 tracer 当参数钻透所有函数
- 预留 `tokens_*` / `cost_usd` 字段，给成本关联（见 03）

Demo：`cli demo` 模拟 retrieve → llm → tool → llm，写出 `lab/out/demo.jsonl`。

## 用到的具体 skill / 技巧清单

| Skill | 用法 |
|-------|------|
| **trace_id / span_id** | `spans.new_id()` |
| **contextvars 传播** | `tracer` 内 `_current` |
| **嵌套 span** | `with tracer.span("tool.calculator"):` |
| **属性白名单思维** | attrs 放可索引字段；敏感值进 redact |
| **status + error** | 失败 span 记 status=error |
| **JSONL 追加写** | 崩溃也不丢已完成 span |
| **usage 挂载点** | `record_usage` |

## 代码解析（按文件路径）

### `lab/src/obs_lab/spans.py`

`Span` dataclass：字段一次对齐，后续 summary / 脱敏都围绕它转。`to_record()` 把 `duration_ms` 物化，避免读盘后再算。

### `lab/src/obs_lab/tracer.py`

- `Tracer(path)`：打开 JSONL
- `span(name, **attrs)`：上下文管理器
- `record_usage(...)`：挂到当前 span

### `lab/src/obs_lab/cli.py`

`demo` / `summary` 子命令。不需要网络。先把时间线建起来，再谈红acted 与成本——顺序见后两篇。
