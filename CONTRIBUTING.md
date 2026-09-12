# Contributing

Thank you for helping improve RichClub Explorer. Contributions should preserve the
project's central principle: statistically consequential choices must be visible,
documented, and tested.

## Before proposing code

Open an issue describing the scientific use case, mathematical definition, expected
behavior, and relevant methodological references. Bug reports should include a
minimal de-identified or synthetic network, software versions, and the random seed.

## Development setup

```bash
git clone https://github.com/adriennekline/richclub-explorer.git
cd richclub-explorer
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[app,dev]"
pytest
ruff check src tests app
```

## Pull requests

- Add tests for new or changed scientific behavior.
- Cite methodological sources for new coefficients or null models.
- Document assumptions and failure modes.
- Do not silently coerce directed, signed, multiplex, or multigraph data.
- Avoid real participant or patient data in tests and examples.
- Keep unrelated changes in separate pull requests.

By contributing, you agree that your contribution is licensed under the project's
BSD 3-Clause License.
