# Configuration

## Path Resolution

This skill uses `CODEX_HOME` for installed files, credentials, virtualenvs, and workspace output. If `CODEX_HOME` is unset, use Codex's usual default:

```bash
export CODEX_HOME="${CODEX_HOME:-$HOME/.codex}"
```

For non-default Linux server installs, export the same `CODEX_HOME` value in the shell or service environment that starts Codex.

## Credential Files

Search credentials:

```text
$CODEX_HOME/credentials/search.json
```

Example:

```json
{
  "grok": {
    "apiUrl": "TODO_OPENAI_COMPATIBLE_BASE_URL",
    "apiKey": "TODO_GROK_API_KEY",
    "model": "grok-4.5",
    "apiFormat": "responses"
  },
  "exa": {
    "apiKey": "TODO_EXA_API_KEY",
    "apiBase": "https://api.exa.ai"
  },
  "tavily": "TODO_TAVILY_API_KEY",
  "openalex": {
    "apiKey": "TODO_OPENALEX_API_KEY"
  }
}
```

MinerU credentials:

```text
$CODEX_HOME/skills/web-search/.env
```

Example:

```bash
MINERU_TOKEN=TODO_MINERU_TOKEN
MINERU_API_BASE=https://mineru.net
# Optional. If unset, MinerU output uses $CODEX_HOME/workspace.
MINERU_WORKSPACE=$CODEX_HOME/workspace
```

## API Key Links

- OpenAI Responses API reference: https://platform.openai.com/docs/api-reference/responses
- AI search MCP reference: https://github.com/lianwusuoai/ai-search-mcp
- Exa: https://dashboard.exa.ai/
- Tavily: https://app.tavily.com/
- MinerU: https://mineru.net/apiManage
- OpenAlex: https://openalex.org/settings/api

## Source Support

`scripts/search.py` directly calls these sources when their keys are configured.

Default source priority:

- Grok-compatible Responses API
- Exa
- Tavily
- OpenAlex

Use `--source grok,exa,tavily,openalex` to force an explicit source set.

There is no separate retrieval selector. By default, the script calls every configured source and uses source priority only for duplicate-resolution and ranking. Use `--source` only when you intentionally want a narrower source set.

Grok uses an OpenAI-compatible Responses API by default. Set `grok.apiUrl` to the third-party base URL, `grok.apiKey` to its API key, `grok.model` to `grok-4.5`, and keep `grok.apiFormat` as `responses`. If a provider only supports Chat Completions, set `grok.apiFormat` to `chat_completions`.

Environment aliases compatible with common AI search MCP setups are also accepted: `AI_API_URL`, `AI_API_KEY`, `AI_SEARCH_MODEL_ID`, `AI_MODEL_ID`, and `AI_API_FORMAT`.

## Runtime

Recommended venv:

```bash
export CODEX_HOME="${CODEX_HOME:-$HOME/.codex}"
python3 -m venv "$CODEX_HOME/venvs/web-search-skill"
"$CODEX_HOME/venvs/web-search-skill/bin/python" -m pip install requests trafilatura beautifulsoup4 lxml
```

The search script checks credentials in this order:

- `WEB_SEARCH_CREDENTIALS`
- `CODEX_SEARCH_CREDENTIALS`
- `$CODEX_HOME/credentials/search.json`
- `./credentials/search.json` from the current working directory
