import json
import tempfile
import unittest
from pathlib import Path

from logforge.engine import analyze_file, parse_line, write_json_report


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
