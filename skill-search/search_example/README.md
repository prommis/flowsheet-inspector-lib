# `search_example`

This directory contains a unified, runnable demo that exercises the new [`skill-search`](..) helper in two phases:

1. Full catalog load:
   read all skills from the configured central catalog and print the discovered list.
2. Iterative discovery:
   load the search tool into a simple LangGraph flow and run several sample requests.

## Prerequisites

- Python 3.11+
- Install example dependencies:

```bash
pip install -r requirements.txt
```

The `skill-search` core itself is path-based and stdlib-only; these dependencies are only for the LangGraph demo layer.

## Run

From this directory:

```bash
python run_demo.py
```

The demo defaults to:

- `--model-endpoint http://localhost:1234/v1`
- `--central-root ../agent-skills-platform/skills`

That makes it runnable inside this repository without rearranging files.

## What The Demo Does

### Phase 1: Full Catalog Load

- calls `../scripts/skill_search.py --load-all --include-prompt`
- prints the merged catalog roots
- prints every discovered skill's name, description, and `SKILL.md` path

### Phase 2: Iterative Discovery

- wraps the same `skill_search.py` script as a search tool
- creates a small LangGraph flow around that tool
- runs three sample tasks by default:
  - `write a hello world file`
  - `extract text from a pdf`
  - `take a screenshot of a local app`

For the hello-world request, the demo also runs the existing `hello-world-writer` bundled script and writes an output file into `./outputs`.

## Model Behavior

If the configured model endpoint is available, the demo uses it for:

- planning a discovery query
- selecting one skill from the discovered candidates

If the model endpoint is unavailable, the demo still runs end to end by falling back to heuristic search and top-result selection.

## Useful Flags

Override the model endpoint (any OpenAI-compatible endpoint):

```bash
python run_demo.py --model-endpoint "http://localhost:1234/v1"
```

Override the central skills root:

```bash
python run_demo.py --central-root /opt/doe/skills
```

Add one or more user-managed roots:

```bash
python run_demo.py \
  --my-skills-path ~/my-team-skills \
  --my-skills-path ~/personal-skills
```

Replace the built-in sample tasks:

```bash
python run_demo.py \
  --sample-task "write a hello world file" \
  --sample-task "summarize sentry issues"
```

## Outputs

Generated files land in:

- `./outputs`

The hello-world sample writes:

- `./outputs/hello_world.txt`
