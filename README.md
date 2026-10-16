# LogForge

LogForge is a Python command-line tool that analyzes application logs, summarizes
severity levels, identifies recurring error messages, and exports JSON reports.

## Requirements

- Python 3.12 or newer

## Installation

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
```

## Usage

Analyze the included sample log and write a JSON report:

```powershell
logforge examples/sample.log --output reports/analysis.json
```

Display available options:

```powershell
logforge --help
```

By default, reports contain aggregate statistics and recurring errors without
storing every parsed event.

To include all parsed events:

```powershell
logforge examples/sample.log --output reports/full-analysis.json --include-events
```

The `--include-events` option uses memory proportional to the number of parsed
events. Unique error messages are also tracked in memory to calculate frequent
errors.

## Output

The JSON report includes:

- Source file path
- Total, parsed, and invalid line counts
- Counts by severity level
- Most frequent error messages and their counts

The command also prints a summary to the terminal.

## Supported log format

```text
YYYY-MM-DD HH:MM:SS LEVEL Message text
```

Supported levels: `DEBUG`, `INFO`, `WARNING`, `ERROR`, and `CRITICAL`.

Malformed entries and invalid timestamps are counted as invalid lines.
Lines longer than 1,000,000 characters are rejected. This limit is fixed and
is not currently configurable.

## Development checks

Run Ruff:

```powershell
ruff check .
```

Run the test suite with coverage:

```powershell
coverage run -m unittest discover -s tests -v
coverage report
```

## Continuous integration

GitHub Actions runs Ruff, verifies the CLI entry point, and runs the test suite
with coverage on pushes, pull requests, and manual workflow dispatches.
The CI job requires at least 95% total code coverage.
