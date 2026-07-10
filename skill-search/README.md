# `skill-search`

`skill-search` is a self-contained, path-based helper for working with a central skills catalog plus optional user-provided skill roots.

It is designed for repositories where a helper directory sits next to a centrally maintained `skills/` directory:

```text
deploy-root/
├── skills/
└── skill-search/
```

## What It Provides

- Full catalog loading:
  returns all merged skill `name`, `description`, and path metadata.
- Iterative search:
  returns only the top matching skills for a query, which keeps the full catalog out of prompt context.
- User override support:
  later roots win when the same skill `name` appears in both the central catalog and a user-managed root.

The core runtime uses only the Python standard library.

## Root Resolution

The helper resolves the central catalog in this order:

1. `--central-root` if provided
2. `SKILL_SEARCH_CENTRAL_ROOT` environment variable
3. sibling `../skills` next to `skill-search`

Optional user-managed roots can be added with repeated `--my-skills-path` flags.

## Script Usage

The stable path-based entrypoint is:

```bash
python scripts/skill_search.py
```

### Full Catalog Load

```bash
python scripts/skill_search.py --load-all --include-prompt
```

With explicit roots:

```bash
python scripts/skill_search.py \
  --central-root ../skills \
  --my-skills-path ~/my-skills \
  --load-all \
  --include-prompt
```

### Iterative Search

```bash
python scripts/skill_search.py --query "wrap methanol_flowsheet.py"
```

With explicit roots:

```bash
python scripts/skill_search.py \
  --central-root ../skills \
  --my-skills-path ~/my-skills \
  --query "how do I import FlowsheetBlock" \
  --top-k 5
```

## Output Format

The script always returns JSON.

Full-load mode returns:

- `mode`
- `central_root`
- `catalog_roots`
- `count`
- `skills`
- `available_skills_prompt` when `--include-prompt` is used

Search mode returns:

- `mode`
- `query`
- `top_k`
- `min_score`
- `central_root`
- `catalog_roots`
- `count`
- `matches`

## As A Skill

This directory includes `SKILL.md` so filesystem-based agents can treat it as a skill wrapper and follow the documented workflow there. To expose this repository's PrOMMiS skills catalog through it, expose `skill-search/` through the agent's skills directory and point the helper at the top-level `skills/` catalog when needed. For native `/<name>` discovery of each skill instead, use the repo's `unpack.sh` (`./unpack.sh --help`).

The importable Python package lives under `skill-search/skill_search/` so the outer directory can keep the validator-friendly hyphenated name.

The frontmatter parser handles single-line scalars, quoted values, YAML folded/literal block scalars (`description: >` / `|`), and a nested `metadata:` block.

## Relationship to `skills-ref`

The `agent-skills-platform/utils/skills-ref` package provides similar catalog, search, and prompt functionality as an installable Python package with `strictyaml` and `click` dependencies.

`skill-search` is intentionally stdlib-only so it can be deployed as a standalone directory alongside a `skills/` catalog without requiring `pip install`. The two packages share the same SKILL.md format and search algorithm but are maintained independently.

## Local Demo

See [`search_example`](search_example) for a runnable end-to-end example that:

- prints the full merged catalog
- loads the iterative search tool into a LangGraph flow
- runs a few simple sample requests
