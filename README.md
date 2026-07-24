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

## Agent Skills

This repository includes PrOMMiS agent skills for common flowsheet development
tasks. These skills give AI agents structured instructions for working with
PrOMMiS flowsheets in a consistent and reviewable way.

The current skills support preparing flowsheets for the Flowsheet Inspector,
making targeted value changes, finding missing imports, and interpreting solver
or diagnostics issues.

- [`skills/`](skills/) contains the PrOMMiS skill folders, including each
  skill's instructions, reference files, and helper scripts.
- [`skill-search/`](skill-search/) contains the command-line search helper that
  matches a plain-English request to the most relevant PrOMMiS skill. 
- See [`skill-search/README.md`](skill-search/README.md) for direct usage details.

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
