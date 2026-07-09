# Pipeline Design Review

This document records the current design choices for the single `web-search` skill.

## Source Priority

Default priority:

```text
Grok > Exa > Tavily > OpenAlex
```

Rationale:

- Grok is the highest-priority quality source for candidate discovery and current context, but generated URLs remain leads that need source verification.
- Exa remains the high-priority semantic retrieval source because it is low-latency and strong for technical/resource retrieval.
- Tavily is the mainstream general-web source.
- OpenAlex is the lower-priority paper-graph source. It is still called by default when configured because the single pipeline is quality-first.

## Adopted From The Earlier Pipeline

- Keep intent classification before retrieval: `factual`, `status`, `comparison`, `tutorial`, `exploratory`, `news`, and `resource`.
- Keep query bundles through `--queries`, especially for comparisons, Chinese technical topics, and broad exploratory tasks.
- Keep a stable `results` contract with `title`, `url`, `snippet`, `published_date`, `source`, optional `meta`, and optional `score`.
- Keep URL deduplication, source labels, freshness scoring, authority scoring, and `--domain-boost`.
- Keep Exa as a single semantic retrieval lane with highlights so ranking has useful snippet text.
- Keep second-stage research synthesis as an additive block after normal retrieval, not a replacement for `results`.
- Keep thread-pulling and citation tracking through `--extract-refs`, `fetch_thread.py`, and `chain_tracker.py`.
- Keep content extraction and MinerU fallback as part of the same single skill.

## Deliberately Rejected

- Multiple skill directories. The current repository is one skill with one root `SKILL.md`.
- Alternative top-level retrieval behaviors. Quality-first multi-source retrieval is the only default behavior.
- Old install paths, old skill names, and legacy runtime config paths.
- Raw web search as an ordinary first step. Raw search is only a fallback when this skill is unavailable or unusable.
- Placeholder features that are not callable from `scripts/search.py`.
- Hiding configured sources behind automatic source gating. Source priority affects ranking, not whether a configured source is attempted.
- Replacing source verification with Grok synthesis. Grok output is useful for leads but not final evidence by itself.
- Adding provider caches, SSRF policy layers, or host-specific runtime integration; this skill is a local script package, not a gateway runtime.
