import io
import sys
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from addrfmt.cli import main


class CliTests(unittest.TestCase):
    def _run(self, stdin_text):
        old_stdin = sys.stdin
        sys.stdin = io.StringIO(stdin_text)
        out, err = io.StringIO(), io.StringIO()
        try:
            with redirect_stdout(out), redirect_stderr(err):
                exit_code = main()
        finally:
            sys.stdin = old_stdin
        return exit_code, out.getvalue(), err.getvalue()

    def test_valid_address_is_printed_normalised(self):
        code, out, err = self._run(
            "Jane Doe\n742 evergreen terrace\nspringfield il 62704-1234\n"
        )
        self.assertEqual(code, 0)
        self.assertEqual(
            out, "Jane Doe\n742 Evergreen Terrace\nSpringfield, IL 62704-1234\n"
        )
        self.assertEqual(err, "")

    def test_invalid_address_reports_error_on_stderr_and_exits_nonzero(self):
        code, out, err = self._run("742 Evergreen Terrace\nSpringfield, Illinois 62704\n")
        self.assertEqual(code, 1)
        self.assertEqual(out, "")
        self.assertIn("line 2, column 14", err)

    def test_empty_stdin_is_reported_as_an_error(self):
        code, out, err = self._run("")
        self.assertEqual(code, 1)
        self.assertEqual(out, "")
        self.assertIn("input is empty", err)


if __name__ == "__main__":
    unittest.main()
