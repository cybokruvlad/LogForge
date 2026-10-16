from __future__ import annotations

import json
import re
from collections import Counter
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterator

LOG_PATTERN = re.compile(
    r"^(?P<timestamp>\d{4}-\d{2}-\d{2} "
    r"\d{2}:\d{2}:\d{2})\s+"
    r"(?P<level>DEBUG|INFO|WARNING|ERROR|CRITICAL)\s+"
    r"(?P<message>.*)$"
)

SUPPORTED_LEVELS = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}


@dataclass(frozen=True, slots=True)
class LogEvent:
    line_number: int
    timestamp: str
    level: str
    message: str


@dataclass(slots=True)
class AnalysisReport:
    source: str
    total_lines: int
    parsed_events: int
    invalid_lines: int
    levels: dict[str, int]
    top_errors: list[dict[str, object]]
    events: list[LogEvent]
    include_events: bool = False

    def to_dict(self) -> dict[str, object]:
        result: dict[str, object] = {
            "source": self.source,
            "total_lines": self.total_lines,
            "parsed_events": self.parsed_events,
            "invalid_lines": self.invalid_lines,
            "levels": self.levels,
            "top_errors": self.top_errors,
        }

        if self.include_events:
            result["events"] = [asdict(event) for event in self.events]

        return result


def parse_line(line: str, line_number: int) -> LogEvent | None:
    match = LOG_PATTERN.fullmatch(line.strip())
    if match is None:
        return None

    timestamp = match.group("timestamp")
    try:
        datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        return None

    return LogEvent(
        line_number=line_number,
        timestamp=timestamp,
        level=match.group("level"),
        message=match.group("message"),
    )


def iter_log_events(path: Path) -> Iterator[tuple[int, LogEvent | None]]:
    with path.open("r", encoding="utf-8-sig", errors="replace") as file:
        for line_number, line in enumerate(file, start=1):
            yield line_number, parse_line(line, line_number)


def analyze_file(
    path: str | Path,
    top: int = 10,
    include_events: bool = False,
) -> AnalysisReport:
    source = Path(path)

    if not source.is_file():
        raise FileNotFoundError(f"Log file not found: {source}")

    if top < 1:
        raise ValueError("top must be at least 1")

    levels: Counter[str] = Counter()
    errors: Counter[str] = Counter()
    events: list[LogEvent] = []
    total_lines = 0
    parsed_events = 0
    invalid_lines = 0

    for _, event in iter_log_events(source):
        total_lines += 1

        if event is None:
            invalid_lines += 1
            continue

        parsed_events += 1
        levels[event.level] += 1

        if include_events:
            events.append(event)

        if event.level in {"ERROR", "CRITICAL"}:
            errors[event.message] += 1

    top_errors = [
        {"message": message, "count": count}
        for message, count in errors.most_common(top)
    ]

    return AnalysisReport(
        source=str(source.resolve()),
        total_lines=total_lines,
        parsed_events=parsed_events,
        invalid_lines=invalid_lines,
        levels={level: levels.get(level, 0) for level in sorted(SUPPORTED_LEVELS)},
        top_errors=top_errors,
        events=events,
        include_events=include_events,
    )


def write_json_report(report: AnalysisReport, output: str | Path) -> Path:
    destination = Path(output)
    destination.parent.mkdir(parents=True, exist_ok=True)

    with destination.open("w", encoding="utf-8", newline="\n") as file:
        json.dump(report.to_dict(), file, indent=2, ensure_ascii=False)
        file.write("\n")

    return destination
