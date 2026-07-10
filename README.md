# Flowsheet Inspector Library
Python package containing library modules and API for the IDAES Flowsheet Inspector user interface.
Developed as part of the Process Optimization & Modeling for Minerals Sustainability (PrOMMiS) initiative ([PrOMMiS website](https://netl.doe.gov/prommis)).

> [!NOTE]
> See `COPYRIGHT.md` and `LICENSE.md` files in this repository before
> downloading, distributing, or otherwise using material from this repository.

## Package layout

- PyPI package name: `idaes-fi`
- Import package: `idaes_fi`
- Source layout: `src/idaes_fi`

## Agent skills

This repository includes an agent-skills catalog for AI coding agents that work
with PrOMMiS and IDAES flowsheet files.

- [`skills/`](skills/) contains the skills catalog. Each skill lives in its own
  directory and includes a `SKILL.md` file that explains when the skill applies
  and what steps an agent should follow.

- [`skill-search/`](skill-search/) contains a lightweight search helper for
  finding the most relevant skill from a plain-English request.

The `.agents/skills/` and `.claude/skills/` wrapper directories expose
`skill-search/` to agents that discover skills from those locations.

See [`skill-search/README.md`](skill-search/README.md) for more details on the
search helper.

## Usage

To run a flowsheet that is wrapped from the shell

```bash
```

## Development

Install in editable mode with test dependencies:

```bash
python -m pip install -e .[dev]
```

Run tests:

```bash
pytest
```

Run static type checking:

```bash
mypy
```
