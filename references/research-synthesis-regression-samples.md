# Research Synthesis Regression Samples

二阶段研究综合边界校准后的回归样本集，用于验证 `_should_run_research_synthesis()` 的命中率和误触发控制。

## 设计原则

- **comparison**: 显式对比语言、判断词或 3+ 子查询 bundle 触发。
- **exploratory**: 判断词、因果词或对比词触发；单纯宽泛主题词不触发。
- **status/news**: 判断词或因果词触发；单纯时效性或多查询扩展不触发。
- **resource/tutorial/factual**: 默认不触发。

## Should Trigger

| ID | Intent | Query | Trigger Signal |
|----|--------|-------|----------------|
| T1 | comparison | Bun vs Deno | explicit "vs" + multi-query |
| T2 | comparison | React 和 Vue 区别 | explicit "区别" |
| T3 | exploratory | RISC-V 生态现在发展到什么阶段，值得持续关注吗？ | "值得" + "关注" judgment |
| T4 | exploratory | AI coding agents landscape 2026, which one should we adopt? | "adopt" judgment |
| T5 | status | OpenAI operator latest progress and impact on developers | "impact" causal |
| T6 | news | AI browser agents this week: what changed and why it matters | "what changed" + "why" causal |

## Should Not Trigger

| ID | Intent | Query | Why Not |
|----|--------|-------|---------|
| N1 | resource | Anthropic MCP official docs | resource intent excluded |
| N2 | tutorial | Rust CLI tutorial | tutorial intent excluded |
| N3 | factual | What is WebTransport | single factual query |
| N4 | factual | What is Model Context Protocol | single factual query |
| N5 | news | OpenAI latest news | news without analysis signal |
| N6 | news | AI news this week 2026 | ordinary news multi-query, no reasoning signal |
| N7 | status | Deno latest status | status without analysis signal |
| N8 | status | PostgreSQL release date | status factual, no reasoning |
| N9 | exploratory | RISC-V ecosystem overview | exploratory without judgment/causal |
| N10 | exploratory | Kubernetes 生态 | broad topic word only |
| N11 | comparison | Bun ecosystem maturity | comparison intent but no compare/judgment signal |
| N12 | status | Deno latest | status multi-query without reasoning signal |

## Validation

Run the detection function against all 18 cases:

```bash
python3 - <<'PY'
import importlib.util
from pathlib import Path

path = Path('scripts/search.py')
spec = importlib.util.spec_from_file_location('search_mod', path)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

cases = [
    {"id":"T1","intent":"comparison","queries":["Bun vs Deno","Bun advantages","Deno advantages"],"expected":True},
    {"id":"T2","intent":"comparison","queries":["React 和 Vue 区别"],"expected":True},
    {"id":"T3","intent":"exploratory","queries":["RISC-V 生态现在发展到什么阶段，值得持续关注吗？"],"expected":True},
    {"id":"T4","intent":"exploratory","queries":["AI coding agents landscape 2026, which one should we adopt?"],"expected":True},
    {"id":"T5","intent":"status","queries":["OpenAI operator latest progress and impact on developers"],"expected":True},
    {"id":"T6","intent":"news","queries":["AI browser agents this week: what changed and why it matters"],"expected":True},
    {"id":"N1","intent":"resource","queries":["Anthropic MCP official docs"],"expected":False},
    {"id":"N2","intent":"tutorial","queries":["Rust CLI tutorial"],"expected":False},
    {"id":"N3","intent":"factual","queries":["What is WebTransport"],"expected":False},
    {"id":"N4","intent":"factual","queries":["What is Model Context Protocol"],"expected":False},
    {"id":"N5","intent":"news","queries":["OpenAI latest news"],"expected":False},
    {"id":"N6","intent":"news","queries":["AI news this week 2026","AI announcement latest"],"expected":False},
    {"id":"N7","intent":"status","queries":["Deno latest status"],"expected":False},
    {"id":"N8","intent":"status","queries":["PostgreSQL release date"],"expected":False},
    {"id":"N9","intent":"exploratory","queries":["RISC-V ecosystem overview"],"expected":False},
    {"id":"N10","intent":"exploratory","queries":["Kubernetes 生态"],"expected":False},
    {"id":"N11","intent":"comparison","queries":["Bun ecosystem maturity"],"expected":False},
    {"id":"N12","intent":"status","queries":["Deno latest","Deno update release"],"expected":False},
]

misses = []
for c in cases:
    observed = mod._should_run_research_synthesis(c['queries'][0], c['queries'], c['intent'])
    status = 'ok' if observed == c['expected'] else 'miss'
    if observed != c['expected']:
        misses.append(c)
    print(f"{c['id']}\t{status}")

if misses:
    print("\n=== MISSES ===")
    for m in misses:
        print(f"{m['id']}: {m['queries'][0]}")
    exit(1)
print("\nAll 18 cases passed")
PY
```

## Changelog

### 2026-07-09

- 删除顶层搜索选择字段后，更新样本和校验函数签名。
- 保留二阶段研究综合的保守触发边界。
