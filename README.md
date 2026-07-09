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

## Path Convention

All install and runtime examples use `$CODEX_HOME`. If you do not set it, use Codex's usual default:

```bash
export CODEX_HOME="${CODEX_HOME:-$HOME/.codex}"
```

If your Linux server starts Codex from a service manager, make sure the Codex process receives the same `CODEX_HOME` value you use during installation.

## Quick Install

Run this from the repository root after cloning or downloading the skill. The command installs or updates source files under `$CODEX_HOME/skills/web-search` and does not overwrite existing credential files.

```bash
export CODEX_HOME="${CODEX_HOME:-$HOME/.codex}"

mkdir -p "$CODEX_HOME/skills" "$CODEX_HOME/credentials" "$CODEX_HOME/workspace" "$CODEX_HOME/venvs"
python3 - <<'PY'
import os
import shutil
from pathlib import Path

src = Path.cwd().resolve()
codex_home = Path(os.environ["CODEX_HOME"]).expanduser().resolve()
dest = (codex_home / "skills" / "web-search").resolve()
dest.mkdir(parents=True, exist_ok=True)

skip_names = {".git", "__pycache__", ".env", "credentials"}

def should_skip(path):
    path = path.resolve()
    return (
        path.name in skip_names
        or path.name.endswith(".pyc")
        or path == dest
        or path in dest.parents
    )

def ignore_dir(dir_path, names):
    ignored = set()
    base = Path(dir_path)
    for name in names:
        if should_skip(base / name):
            ignored.add(name)
    return ignored

if src != dest:
    for item in src.iterdir():
        if should_skip(item):
            continue
        target = dest / item.name
        if item.is_dir():
            shutil.copytree(item, target, dirs_exist_ok=True, ignore=ignore_dir)
        else:
            shutil.copy2(item, target)
PY

python3 -m venv "$CODEX_HOME/venvs/web-search-skill"
"$CODEX_HOME/venvs/web-search-skill/bin/python" -m pip install --upgrade pip
"$CODEX_HOME/venvs/web-search-skill/bin/python" -m pip install requests trafilatura beautifulsoup4 lxml

test -f "$CODEX_HOME/credentials/search.json" || \
  cp "$CODEX_HOME/skills/web-search/references/search-credentials.example.json" "$CODEX_HOME/credentials/search.json"
test -f "$CODEX_HOME/skills/web-search/.env" || \
  cp "$CODEX_HOME/skills/web-search/.env.example" "$CODEX_HOME/skills/web-search/.env"
```

Then edit:

- `$CODEX_HOME/credentials/search.json` for Grok-compatible, Exa, Tavily, and OpenAlex keys.
- `$CODEX_HOME/skills/web-search/.env` only if you want MinerU extraction.

Restart Codex after installation so it loads the new skill.

## Ask Codex To Install It

If you are already using Codex on the target Linux server, you can copy this prompt into Codex from the repository root:

```text
Install this repository as the Codex skill named web-search on this machine.

Use CODEX_HOME from my environment. If CODEX_HOME is unset, set it to $HOME/.codex for the install commands and tell me that default was used. Do not assume ~/.codex when CODEX_HOME is already set.

From the repository root, install or update source files at "$CODEX_HOME/skills/web-search" while preserving existing "$CODEX_HOME/credentials/search.json" and "$CODEX_HOME/skills/web-search/.env". Use a Python standard-library copy step equivalent to the README quick install: exclude .git, __pycache__, .pyc files, .env, and credentials, skip copying if the repository root is already "$CODEX_HOME/skills/web-search", and avoid recursively copying the install destination if it is inside the source tree. Create "$CODEX_HOME/venvs/web-search-skill", install Python dependencies requests, trafilatura, beautifulsoup4, and lxml, and create "$CODEX_HOME/credentials/search.json" and "$CODEX_HOME/skills/web-search/.env" from the example files only if they do not already exist.

After installing, run Python syntax checks for the scripts and run "$CODEX_HOME/venvs/web-search-skill/bin/python" "$CODEX_HOME/skills/web-search/scripts/search.py" --help. Do not overwrite my existing credential files. Tell me exactly which files I need to edit for API keys, then remind me to restart Codex.
```

## Configure

Search credentials live at:

```text
$CODEX_HOME/credentials/search.json
```

Fill any source keys you want enabled. `scripts/search.py` directly calls all configured search sources: Grok-compatible Responses API, Exa, Tavily, and OpenAlex.

Grok uses an OpenAI-compatible Responses API by default. A third-party base URL can be used through `grok.apiUrl`, with `grok.apiKey`, `grok.model`, and optional `grok.apiFormat`.

MinerU credentials live at:

```text
$CODEX_HOME/skills/web-search/.env
```

Fill `MINERU_TOKEN` only if you need MinerU fallback for difficult web pages, PDFs, Office documents, or OCR-heavy content.

## Output Semantics

`scripts/search.py` output distinguishes discovery from verification:

- `results` are search-provider candidate URLs and snippets. They include `retrieval_type: "search_candidate"` and `evidence.level: "candidate"`.
- `refs`, when requested through `--extract-refs` or `--extract-refs-urls`, are fetched source pages used for bounded reference extraction. Each item reports whether the source page was fetched or failed.
- `source_status` records per-query, per-provider configuration, attempt status, result count, and sanitized errors.
- `source_summary` aggregates attempted, successful, missing, and failed provider runs so network or credential failures are not mistaken for empty search results.

## Examples

Commands assume `CODEX_HOME` is exported as shown above.

```bash
"$CODEX_HOME/venvs/web-search-skill/bin/python" "$CODEX_HOME/skills/web-search/scripts/search.py" \
  "OpenAI latest news" --intent news --freshness pw --num 5
```

```bash
"$CODEX_HOME/venvs/web-search-skill/bin/python" "$CODEX_HOME/skills/web-search/scripts/search.py" \
  "retrieval augmented generation evaluation" \
  --source grok,exa,tavily,openalex --num 3
```

## Credits

This Codex skill is adapted from [blessonism/openclaw-search-skills](https://github.com/blessonism/openclaw-search-skills). It keeps the upstream MIT license notice and reworks the original OpenClaw multi-skill layout into one Codex `web-search` skill with Codex-oriented install paths, provider configuration, output semantics, and OpenAlex support.
