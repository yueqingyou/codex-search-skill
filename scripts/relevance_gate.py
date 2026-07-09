#!/usr/bin/env python3
"""
relevance_gate.py — LLM-based relevance scoring for chain tracking.

Given an original query, current knowledge_state, and a list of candidate
links (with anchor_text + context), calls an LLM to batch-score each candidate
and returns only those above the threshold.

Usage (standalone):
  python3 relevance_gate.py \
    --query "Rust async runtime performance" \
    --knowledge "Already know: Tokio vs async-std comparison. Still unclear: real-world benchmarks." \
    --candidates '[{"url":"...","anchor":"...","context":"..."}]' \
    --threshold 0.5

Output JSON:
  [{"url": "...", "anchor": "...", "context": "...", "score": 0.8, "reason": "..."}]
"""

import json
import os
import re
import sys
import argparse
from pathlib import Path
from urllib.parse import urlparse, urlunparse
from urllib.request import Request, urlopen
from urllib.error import HTTPError


DEFAULT_GROK_MODEL = "grok-4.5"


def _expand_path(value: str) -> Path:
    codex_home = os.environ.get("CODEX_HOME") or "~/.codex"
    value = value.replace("${CODEX_HOME}", codex_home).replace("$CODEX_HOME", codex_home)
    return Path(os.path.expanduser(os.path.expandvars(value)))


def _codex_home() -> Path:
    return _expand_path(os.environ.get("CODEX_HOME") or "~/.codex")


def _safe_error_message(error: Exception, max_chars: int = 300) -> str:
    """Render LLM provider errors without leaking tokens."""
    text = str(error)
    text = re.sub(r"(?i)(api_key=)[^&\\s)]+", r"\1<redacted>", text)
    text = re.sub(r"(?i)(authorization['\"]?\\s*[:=]\\s*['\"]?bearer\\s+)[^'\"\\s,)}]+", r"\1<redacted>", text)
    text = re.sub(r"(?i)(bearer\\s+)[a-z0-9._\\-]+", r"\1<redacted>", text)
    return text[:max_chars].rstrip()


# ---------------------------------------------------------------------------
# Credentials loader (reuse search script pattern)
# ---------------------------------------------------------------------------
def _load_creds() -> dict:
    keys = {}
    cred_paths = []
    for env_name in ("WEB_SEARCH_CREDENTIALS", "CODEX_SEARCH_CREDENTIALS"):
        if v := os.environ.get(env_name):
            cred_paths.append(_expand_path(v))
    cred_paths.append(_codex_home() / "credentials" / "search.json")

    for cred_path in cred_paths:
        try:
            cred = json.loads(cred_path.read_text())
            if grok := cred.get("grok"):
                if isinstance(grok, dict):
                    keys["grok_url"] = (
                        grok.get("apiUrl")
                        or grok.get("api_url")
                        or grok.get("baseUrl")
                        or grok.get("base_url")
                        or ""
                    )
                    keys["grok_key"] = grok.get("apiKey") or grok.get("api_key") or ""
                    keys["grok_model"] = (
                        grok.get("model")
                        or grok.get("model_id")
                        or grok.get("search_model_id")
                        or DEFAULT_GROK_MODEL
                    )
                    keys["grok_api_format"] = (
                        grok.get("apiFormat")
                        or grok.get("api_format")
                        or grok.get("endpoint")
                        or "responses"
                    )
            break
        except (json.JSONDecodeError, OSError):
            pass
    # Env var overrides
    for env, key in [("GROK_API_KEY", "grok_key"), ("GROK_API_URL", "grok_url"),
                     ("GROK_MODEL", "grok_model"), ("GROK_API_FORMAT", "grok_api_format")]:
        if v := os.environ.get(env):
            keys[key] = v
    if "grok_key" not in keys and (v := os.environ.get("AI_API_KEY")):
        keys["grok_key"] = v
    if "grok_url" not in keys and (v := os.environ.get("AI_API_URL")):
        keys["grok_url"] = v
    if "grok_model" not in keys and (v := (os.environ.get("AI_SEARCH_MODEL_ID") or os.environ.get("AI_MODEL_ID"))):
        keys["grok_model"] = v
    if "grok_api_format" not in keys and (v := os.environ.get("AI_API_FORMAT")):
        keys["grok_api_format"] = v
    return keys


# ---------------------------------------------------------------------------
# LLM call
# ---------------------------------------------------------------------------
def _normalize_openai_api_format(value: str | None) -> str:
    text = (value or "responses").strip().lower().replace("-", "_")
    if text in {"chat", "chat_completion", "chat_completions"}:
        return "chat_completions"
    return "responses"


def _resolve_openai_endpoint(api_url: str, api_format: str) -> str:
    parsed = urlparse(api_url.rstrip("/"))
    path = parsed.path.rstrip("/")
    target = "/chat/completions" if api_format == "chat_completions" else "/responses"
    if path.endswith(target):
        return urlunparse(parsed)
    return urlunparse(parsed._replace(path=f"{path}{target}" if path else target))


def _extract_text_from_response(data: dict) -> str:
    if isinstance(data.get("output_text"), str):
        return data["output_text"]
    parts = []
    for item in data.get("output") or []:
        if not isinstance(item, dict):
            continue
        for content in item.get("content") or []:
            if isinstance(content, dict) and isinstance(content.get("text"), str):
                parts.append(content["text"])
    if parts:
        return "".join(parts)
    choices = data.get("choices") or []
    if choices:
        return (choices[0].get("message") or {}).get("content") or choices[0].get("text") or ""
    return ""


def _extract_text_from_sse(raw: str) -> str:
    parts = []
    for line in raw.splitlines():
        line = line.strip()
        if not line.startswith("data:"):
            continue
        chunk = line[5:].strip()
        if chunk == "[DONE]":
            break
        try:
            data = json.loads(chunk)
        except json.JSONDecodeError:
            continue
        if isinstance(data.get("delta"), str):
            parts.append(data["delta"])
            continue
        if data.get("type") == "response.output_text.delta" and isinstance(data.get("delta"), str):
            parts.append(data["delta"])
            continue
        choice = (data.get("choices") or [{}])[0]
        delta = choice.get("delta") or choice.get("message") or {}
        if text := (delta.get("content") or choice.get("text")):
            parts.append(text)
    return "".join(parts)


def _call_llm(prompt: str, creds: dict) -> str:
    """Call Grok through an OpenAI-compatible API and return response text."""
    api_key = creds.get("grok_key", "")
    api_url = creds.get("grok_url", "")
    model = creds.get("grok_model", DEFAULT_GROK_MODEL)
    api_format = _normalize_openai_api_format(creds.get("grok_api_format", "responses"))
    url = _resolve_openai_endpoint(api_url, api_format)

    if not api_key:
        raise ValueError("No LLM API key configured (grok_key missing)")
    if not api_url or api_url.lower().startswith("todo_"):
        raise ValueError("No LLM API URL configured (grok_url missing)")

    if api_format == "chat_completions":
        payload_obj = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.1,
            "max_tokens": 1024,
            "stream": False,
        }
    else:
        payload_obj = {
            "model": model,
            "input": prompt,
            "temperature": 0.1,
            "max_output_tokens": 1024,
            "stream": False,
        }
    payload = json.dumps(payload_obj).encode()

    req = Request(url, data=payload, method="POST", headers={
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    })

    try:
        with urlopen(req, timeout=30) as resp:
            raw = resp.read().decode()

        if raw.startswith("data:"):
            return _extract_text_from_sse(raw)

        return _extract_text_from_response(json.loads(raw))

    except HTTPError as e:
        body = e.read().decode() if e.fp else ""
        raise RuntimeError(f"LLM API error {e.code}: {_safe_error_message(Exception(body), 200)}")


# ---------------------------------------------------------------------------
# Prompt builder
# ---------------------------------------------------------------------------
def _build_prompt(query: str, knowledge_state: str, candidates: list) -> str:
    cand_lines = []
    for i, c in enumerate(candidates, 1):
        anchor = c.get("anchor") or c.get("context", "")[:60]
        context = c.get("context", "")[:150]
        url = c.get("url", "")
        cand_lines.append(f'{i}. anchor="{anchor}" url={url}\n   context="{context}"')

    candidates_text = "\n".join(cand_lines)

    return f"""You are a research assistant evaluating whether web links are worth following.

Original query: {query}

What we already know: {knowledge_state or "Nothing yet."}

Candidate links to evaluate:
{candidates_text}

For each candidate, score 0.0-1.0 how likely following this link will provide NEW, RELEVANT information to answer the original query.
- Score > 0.7: definitely follow (directly relevant, likely new info)
- Score 0.4-0.7: maybe follow (somewhat relevant or unclear)
- Score < 0.4: skip (irrelevant, duplicate, or noise)

Respond with ONLY a JSON array, no explanation outside JSON:
[
  {{"id": 1, "score": 0.9, "reason": "one sentence"}},
  {{"id": 2, "score": 0.2, "reason": "one sentence"}},
  ...
]"""


# ---------------------------------------------------------------------------
# Main scoring function
# ---------------------------------------------------------------------------
def score_candidates(
    query: str,
    candidates: list,
    knowledge_state: str = "",
    threshold: float = 0.4,
    creds: dict | None = None,
) -> list:
    """Score candidates and return those above threshold.

    Args:
        query: Original search query.
        candidates: List of {"url", "anchor", "context"} dicts.
        knowledge_state: Summary of what we already know.
        threshold: Minimum score to include (default 0.4).
        creds: API credentials dict (loaded from file if None).

    Returns:
        Filtered + scored list: [{"url", "anchor", "context", "score", "reason"}]
    """
    if not candidates:
        return []

    if creds is None:
        creds = _load_creds()

    prompt = _build_prompt(query, knowledge_state, candidates)

    try:
        raw = _call_llm(prompt, creds)
    except Exception as e:
        # On LLM failure, return all candidates unscored (fail open)
        sys.stderr.write(f"[relevance_gate] LLM call failed: {_safe_error_message(e)}, returning all candidates\n")
        return [dict(c, score=0.5, reason="LLM unavailable") for c in candidates]

    # Parse JSON response
    try:
        # Strip markdown code fences if present
        text = raw.strip()
        if text.startswith("```"):
            text = "\n".join(text.split("\n")[1:])
            text = text.rstrip("`").strip()
        scores = json.loads(text)
    except json.JSONDecodeError:
        sys.stderr.write(f"[relevance_gate] Failed to parse LLM response: {raw[:200]}\n")
        return [dict(c, score=0.5, reason="parse error") for c in candidates]

    # Merge scores back into candidates
    score_map = {item["id"]: item for item in scores if "id" in item}
    result = []
    for i, c in enumerate(candidates, 1):
        s = score_map.get(i, {})
        score = float(s.get("score", 0.5))
        if score >= threshold:
            result.append({
                **c,
                "score": score,
                "reason": s.get("reason", ""),
            })

    # Sort by score descending
    result.sort(key=lambda x: x["score"], reverse=True)
    return result


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser(description="LLM relevance gate for chain tracking")
    ap.add_argument("--query", required=True, help="Original search query")
    ap.add_argument("--knowledge", default="", help="Current knowledge state summary")
    ap.add_argument("--candidates", required=True,
                    help='JSON array of {"url","anchor","context"} objects')
    ap.add_argument("--threshold", type=float, default=0.4,
                    help="Minimum score threshold (default 0.4)")
    args = ap.parse_args()

    try:
        candidates = json.loads(args.candidates)
    except json.JSONDecodeError as e:
        print(json.dumps({"error": f"Invalid candidates JSON: {e}"}))
        sys.exit(1)

    creds = _load_creds()
    results = score_candidates(
        query=args.query,
        candidates=candidates,
        knowledge_state=args.knowledge,
        threshold=args.threshold,
        creds=creds,
    )
    print(json.dumps(results, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
