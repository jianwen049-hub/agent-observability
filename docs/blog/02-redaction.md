# 02 · 日志里的手机号与密钥：脱敏怎么做

## 当时我怎么看这个问题

第一次把 prompt / tool 参数写进 trace 时，我几乎原样 dump。理由很朴素：排障时越完整越好。一周后做安全自查，JSONL 里出现了手机号、邮箱，还有一次有人把 `Authorization: Bearer ...` 粘进了工具错误信息。更糟的是，这份 trace 已经被复制到另一台调试机——「事后删除」追不回副本。

那时我才意识到一个悖论：**trace 越有用，就越像一份敏感数据仓库。** 可观测性如果默认不安全，团队要么不敢记（回到黑盒），要么埋下合规雷。

## 试过什么

1. **事后人工删 / grep 清洗**：不可扩展，且已扩散的文件追不回；还容易漏掉变体格式（带空格的 Bearer、用 `apiKey` 驼峰的字段）。
2. **整字段丢弃**：例如从不记录 `input`、`error`——排障立刻瞎，尤其是 tool 参数错误这类问题。
3. **加密整条 span**：查询与 grep 变痛，本地 lab 和 CI 都变重，密钥管理又引入新问题。
4. **只靠访问控制**：桶权限再严，也解决不了「开发者笔记本上的明文 JSONL」。

## 为什么否决

否决「先记下来以后再说」。否决「全部不记」。否决「靠权限代替脱敏」。要的是**写入前同步脱敏**：默认安全，同时保留排障足够的结构（模型名、路由、耗时、token、错误类型），正文用占位符或截断预览。

## 最终怎么解

`lab/src/obs_lab/redact.py` 在 tracer 写盘前跑一遍：

- 手机号、邮箱等模式 → `[REDACTED_PHONE]` / `[REDACTED_EMAIL]`
- `sk-` / `Bearer` 赋值 → 截断
- 键名含 `password` / `secret` / `token` / `api_key` → 整值替换
- 递归处理 dict / list / str
- 长文本可另做「前 80 字 + hash」预览（本仓先做正则层，预留扩展）

Tracer 的 `span` attrs 在进入时就 `redact_obj`，避免业务代码「忘了调一次」。这是刻意的安全默认：比文档提醒可靠。

## 用到的具体 skill / 技巧清单

| Skill | 用法 |
|-------|------|
| **写入前 redact** | `redact.redact_obj` 挂在 tracer 出口 |
| **正则模式库** | 手机 / 邮箱 / bearer / sk- |
| **键名启发式** | 敏感 key 直接红acted，不依赖值形态 |
| **递归结构** | tool args 经常是嵌套 JSON |
| **不可逆默认** | lab 不提供「解密回放」 |
| **单测锁红线** | smoke 断言明文手机号永不出现在 JSONL |

## 代码解析（按文件路径）

### `lab/src/obs_lab/redact.py`

`redact_text(s)` 处理字符串；`redact_obj(o, key=...)` 递归。键名启发式与值正则互补——有时 token 在无关键 key 的长字符串里，有时在标准字段里。

### `lab/src/obs_lab/tracer.py` 的衔接

`span` 上下文管理器在创建 attrs 与异常 message 上都走 redact。`cli demo` 故意塞一个手机号字段，再用 smoke 读回文件确认已被替换。

### `lab/scripts/smoke_check.py`

这不是锦上添花：脱敏如果只靠人工 spot check，回归时一定漏。CI/本地一键 grepping 输出是最低成本的安全网。

脱敏不是「日志少写点」，而是**让团队敢于把 span 记全，又不怕把密钥记进去**。
