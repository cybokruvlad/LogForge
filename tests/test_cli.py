import contextlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from logforge.cli import main


class CliTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.root = Path(self.temp_dir.name)
        self.source = self.root / "sample.log"
        self.source.write_text(
            "2026-10-16 10:00:00 INFO Started\n"
            "2026-10-16 10:00:01 ERROR Failed\n",
            encoding="utf-8",
        )
        self.output = self.root / "reports" / "report.json"

    def run_cli(self, *args):
        stdout = io.StringIO()
        stderr = io.StringIO()
        with patch.object(sys, "argv", ["logforge", *map(str, args)]):
            with contextlib.redirect_stdout(stdout):
                with contextlib.redirect_stderr(stderr):
                    code = main()
        return code, stdout.getvalue(), stderr.getvalue()

    def test_successful_summary_report(self):
        code, stdout, stderr = self.run_cli(
            self.source, "--output", self.output
        )
        self.assertEqual(code, 0)
        self.assertEqual(stderr, "")
        result = json.loads(stdout)
        self.assertEqual(result["parsed_events"], 2)
        payload = json.loads(self.output.read_text(encoding="utf-8"))
        self.assertNotIn("events", payload)

    def test_include_events_option(self):
        code, stdout, _ = self.run_cli(
            self.source,
            "--output", self.output,
            "--include-events",
        )
        self.assertEqual(code, 0)
        self.assertTrue(json.loads(stdout)["include_events"])
        payload = json.loads(self.output.read_text(encoding="utf-8"))
        self.assertEqual(len(payload["events"]), 2)

    def test_missing_input_returns_error(self):
        missing = self.root / "missing.log"
        code, stdout, stderr = self.run_cli(
            missing, "--output", self.output
        )
        self.assertEqual(code, 2)
        self.assertEqual(stdout, "")
        self.assertIn("Log file not found", stderr)

    def test_invalid_top_returns_error(self):
        code, stdout, stderr = self.run_cli(
            self.source, "--output", self.output, "--top", "0"
        )
        self.assertEqual(code, 2)
        self.assertEqual(stdout, "")
        self.assertIn("top must be at least 1", stderr)


if __name__ == "__main__":
    unittest.main()
