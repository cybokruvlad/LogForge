from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .engine import analyze_file, write_json_report


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="logforge",
        description="Analyze application logs and generate a JSON report.",
    )
    parser.add_argument("logfile", type=Path, help="Path to the log file")
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("reports/analysis.json"),
        help="JSON report destination",
    )
    parser.add_argument(
        "--top",
        type=int,
        default=10,
        help="Number of frequent error messages to include",
    )
    parser.add_argument(
        "--include-events",
        action="store_true",
        help="Include every parsed event in the JSON report (uses more memory)",
    )
    args = parser.parse_args()

    try:
        report = analyze_file(
            args.logfile,
            top=args.top,
            include_events=args.include_events,
        )
        destination = write_json_report(report, args.output)
    except (OSError, ValueError) as exc:
        print(f"logforge: error: {exc}", file=sys.stderr)
        return 2

    print(json.dumps({
        "source": report.source,
        "total_lines": report.total_lines,
        "parsed_events": report.parsed_events,
        "invalid_lines": report.invalid_lines,
        "levels": report.levels,
        "include_events": report.include_events,
        "report": str(destination.resolve()),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
