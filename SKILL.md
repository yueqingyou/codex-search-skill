---
name: web-search
description: >
  Use for web search, online lookup, fact checking, current information, news,
  technical research, comparisons, resource discovery, and citation-chain tracking.
  For pure web-search tasks, use this skill before raw web_search/web search and
  do not call raw web_search unless this skill is unavailable or cannot run. This
  skill can still use browser, MCP, GitHub, external search connectors, or document
  extraction tools when those are the right non-raw-search tool for the task.
---

# Web Search

Use this as the default search workflow. It replaces direct raw web search for search-shaped tasks, while still allowing other tools when they are better suited to the job.

## Policy

- For pure web search, lookup, current information, factual verification, news, comparison, and source-finding tasks, run this skill first.
- Do not call raw `web_search` or equivalent raw search directly unless this skill is unavailable, missing dependencies, missing all usable keys, or clearly cannot satisfy the request.
- Source priority is `Grok > Exa > Tavily > OpenAlex`.
- There is no separate retrieval selector. The default behavior is quality-first multi-source retrieval.
- OpenAlex is the supplemental paper-graph source. Use it explicitly or when the query is about papers, DOI, literature, citations, journals, or scholarly review.
- Browser automation remains appropriate for interactive pages, login/session-bound pages, visual verification, JS-heavy sites, or workflows where the page state matters.
- MCP, GitHub, Notion, literature, database, and other domain connectors remain appropriate when they provide native structured access to the target system.
- External search tools remain appropriate as supplemental sources or when explicitly requested, but merge and verify their results through this skill's source-ranking and synthesis workflow when practical.
- Grok-generated URLs are candidate leads, not final evidence. Important claims need source-level verification.
- Ordinary `scripts/search.py` results are candidate URLs and snippets. Use `source_status` / `source_summary` to distinguish provider failures from empty results, and use fetched pages, official documents, or domain APIs before treating important claims as verified.

## Scripts

Run scripts from the skill root or use absolute paths after installation.
Commands assume `CODEX_HOME` is exported. If it is unset, set it before running the examples; README documents the default.

```bash
"$CODEX_HOME/venvs/web-search-skill/bin/python" "$CODEX_HOME/skills/web-search/scripts/search.py" "query" --intent exploratory --num 5
```

Available scripts:

- `scripts/search.py`：Exa、Tavily、Grok 兼容源、OpenAlex 多源检索、去重、评分、二阶段研究综合和引用提取入口。
- `scripts/fetch_thread.py`：完整抓取 GitHub issue/PR、HN、Reddit、V2EX 和普通网页。
- `scripts/chain_tracker.py`：沿引用图做受限广度追踪。
- `scripts/relevance_gate.py`：用 Grok 兼容源给待追踪链接打分；缺 key 时 fail open。
- `scripts/content_extract.py`：URL 到 Markdown 的统一包装；普通抓取不可靠时调用 MinerU。
- `scripts/mineru_parse_documents.py`：MinerU 官方 API 的多 URL JSON 包装。
- `scripts/mineru_extract.py`：MinerU 官方 API 的单 URL 低层命令。

## Credentials

Primary search credentials file:

```text
$CODEX_HOME/credentials/search.json
```

Environment overrides:

```bash
export WEB_SEARCH_CREDENTIALS="/path/to/search.json"
export CODEX_SEARCH_CREDENTIALS="/path/to/search.json"
export GROK_API_URL="https://your-compatible-provider.example/v1"
export GROK_API_KEY="..."
export GROK_MODEL="grok-4.5"
export GROK_API_FORMAT="responses"
export EXA_API_KEY="..."
export EXA_API_BASE="https://api.exa.ai"
export TAVILY_API_KEY="..."
export OPENALEX_API_KEY="..."
```

MinerU token lives in the skill root `.env` or environment:

```bash
MINERU_TOKEN=...
MINERU_API_BASE=https://mineru.net
MINERU_WORKSPACE=$CODEX_HOME/workspace
```

For setup details and API key links, read `references/configuration.md`.

## Search Workflow

Pipeline:

1. Intent classification: choose `factual`, `status`, `comparison`, `tutorial`, `exploratory`, `news`, or `resource`.
2. Query expansion: use `--queries` for comparisons, Chinese technical queries, and ambiguous exploratory topics. Keep expansion small unless the task clearly needs breadth.
3. Retrieval: run the single quality-first pipeline. It calls every configured source unless `--source` narrows the source set.
4. Source routing: use Grok for highest-quality candidate leads, Exa for high-priority semantic retrieval, Tavily for mainstream web coverage, and OpenAlex for paper graph coverage.
5. Merge and rank: rely on `scripts/search.py` URL deduplication, source-priority tie breaking, intent-aware scoring, domain authority, freshness, and `--domain-boost` when needed.
6. Add synthesis carefully: run second-stage research synthesis only after ordinary retrieval for comparison/exploratory/status/news queries with judgment, causal, or multi-query signals.
7. Trace and extract: use `--extract-refs`, `fetch_thread.py`, and `content_extract.py` when first-hop results point to issues, PRs, forum threads, papers, PDFs, or anti-bot pages.
8. Interpret output semantics: `results` are `search_candidate` entries with `evidence.level=candidate`; fetched `refs` entries report source-page fetch status.
9. Verify and synthesize: verify important claims against source pages or official documents, then synthesize by topic and reliability rather than by provider.

Recommended intent settings:

| Intent | Freshness | Notes |
|--------|-----------|-------|
| `factual` | none | Prefer official and canonical explanations. |
| `status` | `pw` or `pm` | Use for latest/current state. |
| `comparison` | `py` | Use multi-query bundles. |
| `tutorial` | `py` | Prefer official docs and maintained guides. |
| `exploratory` | optional | Use second-stage synthesis only for analysis/judgment-heavy queries. |
| `news` | `pd` or `pw` | Require source-date checking. |
| `resource` | none | Prefer official and canonical URLs. |

## Commands

Multi-source search:

```bash
"$CODEX_HOME/venvs/web-search-skill/bin/python" "$CODEX_HOME/skills/web-search/scripts/search.py" \
  "RAG framework comparison" --intent exploratory --num 5
```

Fresh search:

```bash
"$CODEX_HOME/venvs/web-search-skill/bin/python" "$CODEX_HOME/skills/web-search/scripts/search.py" \
  "Deno latest release" --intent status --freshness pw --num 5
```

Single-source test:

```bash
"$CODEX_HOME/venvs/web-search-skill/bin/python" "$CODEX_HOME/skills/web-search/scripts/search.py" \
  "OpenAI latest news" --source grok --num 5
```

Explicit multi-source test:

```bash
"$CODEX_HOME/venvs/web-search-skill/bin/python" "$CODEX_HOME/skills/web-search/scripts/search.py" \
  "retrieval augmented generation evaluation" \
  --source grok,exa,tavily,openalex --num 3
```

Exa-only retrieval:

```bash
"$CODEX_HOME/venvs/web-search-skill/bin/python" "$CODEX_HOME/skills/web-search/scripts/search.py" \
  "official Model Context Protocol documentation" --source exa --intent resource --num 5
```

Citation tracking:

```bash
"$CODEX_HOME/venvs/web-search-skill/bin/python" "$CODEX_HOME/skills/web-search/scripts/search.py" \
  "GitHub issue root cause analysis" --intent status --extract-refs
```

Fetch a full thread:

```bash
"$CODEX_HOME/venvs/web-search-skill/bin/python" "$CODEX_HOME/skills/web-search/scripts/fetch_thread.py" \
  "https://github.com/owner/repo/issues/123" --format markdown
```

Extract web content:

```bash
"$CODEX_HOME/venvs/web-search-skill/bin/python" "$CODEX_HOME/skills/web-search/scripts/content_extract.py" \
  --url "https://mp.weixin.qq.com/s/example" --model MinerU-HTML
```

Parse a document with MinerU:

```bash
"$CODEX_HOME/venvs/web-search-skill/bin/python" "$CODEX_HOME/skills/web-search/scripts/mineru_parse_documents.py" \
  --file-sources "https://example.com/paper.pdf" --model-version pipeline --emit-markdown --max-chars 20000
```

## References

- Read `references/intent-guide.md` when query classification is ambiguous.
- Read `references/pipeline-design.md` when changing source priority, retrieval phases, or provider scope.
- Read `references/authority-domains.json` when tuning domain authority.
- Read `references/domain-whitelist.md` and `references/content-heuristics.md` when deciding whether to use MinerU.
- Read `references/configuration.md` when setting up credentials or explaining API key acquisition.
