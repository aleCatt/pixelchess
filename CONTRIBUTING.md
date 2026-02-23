# Contributing

Thanks for taking the time. Here's what you need to know.

## Ground rules

- One concern per pull request.
- All new behaviour should have a corresponding test in `tests/`.
- The chess layer (`chess/`) must stay free of pygame imports. Any rendering or input concern belongs in the GUI layer.
- Keep commits small and their messages imperative: `Add en passant test`, not `Added tests for en passant stuff`.

## Setting up

```bash
git clone https://github.com/AleCatt/pixelchess.git
cd pixelchess
pip install -r requirements.txt
pip install pytest
```

Run tests before and after your change:

```bash
pytest tests/
```

## Reporting bugs

Use the [bug report template](.github/ISSUE_TEMPLATE/bug_report.md). Include the Python and pygame versions, your OS, and exact steps to reproduce.

## Proposing features

Open an issue using the [feature request template](.github/ISSUE_TEMPLATE/feature_request.md) before writing code. This avoids duplicate effort and lets us agree on scope upfront.

## Code style

- Follow [PEP 8](https://peps.python.org/pep-0008/).
- Type-annotate all public function signatures.
- No explanatory comments for things that are clear from the code. Comments should explain *why*, not *what*.
- Max line length: 100 characters.
