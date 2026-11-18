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

## Usage

See the :book:[online documentation](https://flowsheet-inspector-lib.readthedocs.io/en/latest/index.html):book:

The documentation is built from the `docs` directory of this repository and hosted by [Read the Docs](https://about.readthedocs.com/).

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
