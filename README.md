# LogForge

A Python log-analysis engine for parsing application logs, summarizing severity
levels, identifying recurring error messages, and exporting JSON reports.

## Requirements

- Python 3.12 or newer

## Install

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
```

## Run

```powershell
logforge examples/sample.log --output reports/analysis.json
```

By default, reports contain aggregate statistics and recurring errors, not every
parsed event.

To include all parsed events:

```powershell
logforge examples/sample.log --output reports/full-analysis.json --include-events
```

Including events uses memory proportional to the number of parsed events.

## Test

```powershell
ruff check .
coverage run -m unittest discover -s tests -v
coverage report
```

## Supported log format

```text
YYYY-MM-DD HH:MM:SS LEVEL Message text
```

Supported levels: DEBUG, INFO, WARNING, ERROR, CRITICAL.

Malformed entries and invalid timestamps are counted as invalid lines.

## Current limitations

- Unique error messages are counted in memory to calculate the most frequent errors.
- The `--include-events` option retains all parsed events in memory.
- Only one documented log format is supported.
- Input line length is not configurable yet.

## Continuous integration

GitHub Actions runs Ruff and the test suite with coverage on pushes,
pull requests, and manual workflow dispatches.
