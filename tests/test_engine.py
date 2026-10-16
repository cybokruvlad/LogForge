import json
import tempfile
import unittest
from pathlib import Path

from logforge.engine import analyze_file, iter_log_events, parse_line, write_json_report


class LogForgeTests(unittest.TestCase):
    def test_parse_valid_line(self):
        event = parse_line(
            "2026-10-16 10:00:00 ERROR Connection failed", 7
        )
        self.assertIsNotNone(event)
        assert event is not None
        self.assertEqual(event.line_number, 7)
        self.assertEqual(event.level, "ERROR")
        self.assertEqual(event.message, "Connection failed")

    def test_reject_malformed_line(self):
        self.assertIsNone(parse_line("not a log entry", 1))

    def test_reject_invalid_timestamp(self):
        self.assertIsNone(
            parse_line("2026-13-45 10:00:00 ERROR Bad date", 1)
        )

    def test_analyze_counts_and_repeated_errors(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "test.log"
            path.write_text(
                "2026-10-16 10:00:00 INFO Started\n"
                "2026-10-16 10:00:01 ERROR Failed\n"
                "2026-10-16 10:00:02 ERROR Failed\n"
                "malformed\n",
                encoding="utf-8",
            )
            report = analyze_file(path)
            self.assertEqual(report.total_lines, 4)
            self.assertEqual(report.parsed_events, 3)
            self.assertEqual(report.invalid_lines, 1)
            self.assertEqual(report.levels["ERROR"], 2)
            self.assertEqual(report.top_errors[0]["count"], 2)

    def test_default_report_does_not_store_events(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "test.log"
            path.write_text(
                "2026-10-16 10:00:00 INFO Started\n"
                "2026-10-16 10:00:01 ERROR Failed\n",
                encoding="utf-8",
            )
            report = analyze_file(path)
            self.assertEqual(report.parsed_events, 2)
            self.assertEqual(report.events, [])
            self.assertNotIn("events", report.to_dict())

    def test_include_events_is_opt_in(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "test.log"
            path.write_text(
                "2026-10-16 10:00:00 INFO Started\n",
                encoding="utf-8",
            )
            report = analyze_file(path, include_events=True)
            self.assertEqual(len(report.events), 1)
            self.assertEqual(len(report.to_dict()["events"]), 1)

    def test_write_json_report(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "test.log"
            source.write_text(
                "2026-10-16 10:00:00 INFO Started\n", encoding="utf-8"
            )
            report = analyze_file(source)
            destination = write_json_report(report, root / "out" / "report.json")
            payload = json.loads(destination.read_text(encoding="utf-8"))
            self.assertEqual(payload["parsed_events"], 1)
            self.assertNotIn("events", payload)
            self.assertTrue(destination.is_file())

    def test_oversized_line_is_invalid_and_analysis_continues(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "oversized.log"
            oversized_line = (
                "2026-10-16 10:00:00 ERROR " + ("X" * 1_000_001)
            )
            valid_line = "2026-10-16 10:00:01 INFO Service recovered"
            path.write_text(
                oversized_line + "\n" + valid_line + "\n",
                encoding="utf-8",
            )

            report = analyze_file(path)

            self.assertEqual(report.total_lines, 2)
            self.assertEqual(report.invalid_lines, 1)
            self.assertEqual(report.parsed_events, 1)
            self.assertEqual(report.levels["INFO"], 1)

    def test_oversized_line_at_eof_without_newline_is_invalid(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "oversized-eof.log"
            path.write_text(
                "2026-10-16 10:00:00 ERROR " + ("X" * 1_000_001),
                encoding="utf-8",
            )

            report = analyze_file(path)

            self.assertEqual(report.total_lines, 1)
            self.assertEqual(report.invalid_lines, 1)
            self.assertEqual(report.parsed_events, 0)

    def test_line_at_maximum_length_is_accepted(self):
        from logforge.engine import MAX_LINE_LENGTH

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "boundary.log"
            prefix = "2026-10-16 10:00:00 INFO "
            line = prefix + ("X" * (MAX_LINE_LENGTH - len(prefix)))
            path.write_text(line + "\n", encoding="utf-8")

            report = analyze_file(path)

            self.assertEqual(report.total_lines, 1)
            self.assertEqual(report.parsed_events, 1)
            self.assertEqual(report.invalid_lines, 0)

    def test_iterator_rejects_oversized_line_and_continues(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "reader.log"
            oversized = "2026-10-16 10:00:00 ERROR " + ("X" * 1_000_001)
            valid = "2026-10-16 10:00:01 INFO Recovered"
            path.write_text(oversized + "\n" + valid + "\n", encoding="utf-8")

            events = list(iter_log_events(path))

            self.assertEqual(len(events), 2)
            self.assertIsNone(events[0][1])
            self.assertIsNotNone(events[1][1])

    def test_iterator_accepts_line_at_exact_limit(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "boundary.log"
            prefix = "2026-10-16 10:00:00 INFO "
            line = prefix + ("X" * (1_000_000 - len(prefix)))
            path.write_text(line + "\n", encoding="utf-8")

            events = list(iter_log_events(path))

            self.assertEqual(len(events), 1)
            self.assertIsNotNone(events[0][1])

    def test_missing_file(self):
        with self.assertRaises(FileNotFoundError):
            analyze_file("definitely-missing-logforge-file.log")

    def test_invalid_top(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "test.log"
            path.write_text("", encoding="utf-8")
            with self.assertRaises(ValueError):
                analyze_file(path, top=0)


if __name__ == "__main__":
    unittest.main()
