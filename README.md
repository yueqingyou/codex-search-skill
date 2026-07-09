# Web Search Skill

Single Codex skill for web-search-first workflows. It replaces raw web search for search-shaped tasks while still allowing browser, MCP, GitHub, literature, and other domain tools when those are the right tool for the job.

## What It Does

- Runs multi-source search across Grok-compatible Responses API, Exa, Tavily, and OpenAlex.
- Uses source priority `Grok > Exa > Tavily > OpenAlex`.
- Uses one quality-first pipeline that calls every configured source unless `--source` narrows the source set.
- Scores, deduplicates, and ranks results with intent-aware weighting.
- Labels ordinary search hits as candidate URLs and reports provider status in structured output.
- Supports GitHub/forum/thread fetching and citation-chain extraction.
- Falls back to MinerU for difficult web pages, PDFs, Office documents, and OCR-heavy content.

## Install

```bash
mkdir -p ~/.codex/skills ~/.codex/credentials ~/.codex/workspace ~/.codex/venvs
cp -R . ~/.codex/skills/web-search
python3 -m venv ~/.codex/venvs/web-search-skill
~/.codex/venvs/web-search-skill/bin/python -m pip install requests trafilatura beautifulsoup4 lxml
```

Restart Codex after installation.

## Configure

Copy `references/search-credentials.example.json` to:

```text
~/.codex/credentials/search.json
```

Fill any source keys you want enabled. `scripts/search.py` directly calls all configured search sources: Grok-compatible Responses API, Exa, Tavily, and OpenAlex.

Grok uses an OpenAI-compatible Responses API by default. A third-party base URL can be used through `grok.apiUrl`, with `grok.apiKey`, `grok.model`, and optional `grok.apiFormat`.

For MinerU, copy `.env.example` to:

```text
~/.codex/skills/web-search/.env
```

Then fill `MINERU_TOKEN`.

## Output Semantics

`scripts/search.py` output distinguishes discovery from verification:

- `results` are search-provider candidate URLs and snippets. They include `retrieval_type: "search_candidate"` and `evidence.level: "candidate"`.
- `refs`, when requested through `--extract-refs` or `--extract-refs-urls`, are fetched source pages used for bounded reference extraction. Each item reports whether the source page was fetched or failed.
- `source_status` records per-query, per-provider configuration, attempt status, result count, and sanitized errors.
- `source_summary` aggregates attempted, successful, missing, and failed provider runs so network or credential failures are not mistaken for empty search results.

## Examples

```bash
~/.codex/venvs/web-search-skill/bin/python ~/.codex/skills/web-search/scripts/search.py \
  "OpenAI latest news" --intent news --freshness pw --num 5
```

```bash
~/.codex/venvs/web-search-skill/bin/python ~/.codex/skills/web-search/scripts/search.py \
  "retrieval augmented generation evaluation" \
  --source grok,exa,tavily,openalex --num 3
```

## Credits

This skill was built with reference to and appreciation for [blessonism/openclaw-search-skills](https://github.com/blessonism/openclaw-search-skills).
