import sys
import unittest
from pathlib import Path

# Package isn't installed anywhere in CI or on a fresh checkout, so make the
# src layout importable without needing `pip install -e .` first.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from addrfmt import AddressFormatError, format_address, parse_address


class ParseSuccessTests(unittest.TestCase):
    def test_basic_two_line_address(self):
        text = "Jane Doe\n742 evergreen terrace\nspringfield, il 62704-1234"
        parsed = parse_address(text)
        self.assertEqual(parsed.lines, ("Jane Doe", "742 Evergreen Terrace"))
        self.assertEqual(parsed.city, "Springfield")
        self.assertEqual(parsed.state, "IL")
        self.assertEqual(parsed.zip_code, "62704-1234")

    def test_format_address_matches_readme_example(self):
        text = "Jane Doe\n742 evergreen terrace\nspringfield il 62704-1234"
        self.assertEqual(
            format_address(text),
            "Jane Doe\n742 Evergreen Terrace\nSpringfield, IL 62704-1234",
        )

    def test_comma_before_state_is_optional(self):
        parsed = parse_address("100 Main St\nChicago IL 60601")
        self.assertEqual(parsed.city, "Chicago")
        self.assertEqual(parsed.state, "IL")

    def test_five_digit_zip_without_plus_four(self):
        parsed = parse_address("100 Main St\nChicago, IL 60601")
        self.assertEqual(parsed.zip_code, "60601")

    def test_hyphenated_city_name_is_titlecased_per_part(self):
        parsed = parse_address("1 Main St\nwinston-salem, nc 27101")
        self.assertEqual(parsed.city, "Winston-Salem")

    def test_internal_whitespace_is_collapsed(self):
        parsed = parse_address("123   Main\tSt\nChicago, IL 60601")
        self.assertEqual(parsed.lines, ("123 Main St",))

    def test_blank_lines_between_content_are_ignored_for_output(self):
        text = "742 Main St\n\nChicago, IL 60601\n"
        parsed = parse_address(text)
        self.assertEqual(parsed.lines, ("742 Main St",))
        self.assertEqual(parsed.city, "Chicago")

    def test_directionals_are_uppercased(self):
        parsed = parse_address("123 nw Elm St\nPortland, OR 97201")
        self.assertEqual(parsed.lines, ("123 NW Elm St",))

    def test_all_compass_directionals_are_uppercased(self):
        parsed = parse_address("1 Main St\nApt 2 se\nPortland, OR 97201")
        self.assertEqual(parsed.lines, ("1 Main St", "Apt 2 SE"))

    def test_directional_with_trailing_comma_is_uppercased(self):
        parsed = parse_address("1 Main St Nw, Suite 2\nPortland, OR 97201")
        self.assertEqual(parsed.lines, ("1 Main St NW, Suite 2",))

    def test_single_street_line_has_no_recipient(self):
        parsed = parse_address("100 Main St\nChicago, IL 60601")
        self.assertEqual(parsed.recipient_lines, ())
        self.assertEqual(parsed.street_lines, ("100 Main St",))

    def test_recipient_line_split_from_street_line(self):
        parsed = parse_address("Jane Doe\n742 Evergreen Terrace\nSpringfield, IL 62704")
        self.assertEqual(parsed.recipient_lines, ("Jane Doe",))
        self.assertEqual(parsed.street_lines, ("742 Evergreen Terrace",))

    def test_lines_after_street_are_kept_with_street(self):
        text = "Jane Doe\n742 Evergreen Terrace\nApt 4\nSpringfield, IL 62704"
        parsed = parse_address(text)
        self.assertEqual(parsed.recipient_lines, ("Jane Doe",))
        self.assertEqual(parsed.street_lines, ("742 Evergreen Terrace", "Apt 4"))

    def test_po_box_counts_as_street_start(self):
        text = "Jane Doe\nPO Box 42\nSpringfield, IL 62704"
        parsed = parse_address(text)
        self.assertEqual(parsed.recipient_lines, ("Jane Doe",))
        self.assertEqual(parsed.street_lines, ("PO Box 42",))

    def test_no_recognisable_street_line_falls_back_to_last_line(self):
        text = "Jane Doe\nRural Route Two\nSpringfield, IL 62704"
        parsed = parse_address(text)
        self.assertEqual(parsed.recipient_lines, ("Jane Doe",))
        self.assertEqual(parsed.street_lines, ("Rural Route Two",))


class ParseErrorTests(unittest.TestCase):
    def test_empty_input(self):
        with self.assertRaises(AddressFormatError) as cm:
            parse_address("")
        err = cm.exception
        self.assertEqual((err.line, err.column), (1, 1))
        self.assertEqual(err.source_line, "")

    def test_whitespace_only_input(self):
        with self.assertRaises(AddressFormatError) as cm:
            parse_address("   \n\t\n")
        self.assertEqual(cm.exception.line, 1)

    def test_single_line_input_is_rejected(self):
        with self.assertRaises(AddressFormatError) as cm:
            parse_address("Springfield, IL 62704")
        err = cm.exception
        self.assertEqual(err.line, 1)
        self.assertIn("at least one line", err.message)

    def test_missing_zip_reports_end_of_line(self):
        with self.assertRaises(AddressFormatError) as cm:
            parse_address("123 Main St\nChicago, IL")
        err = cm.exception
        self.assertEqual(err.line, 2)
        self.assertEqual(err.column, 12)
        self.assertEqual(err.source_line, "Chicago, IL")

    def test_missing_zip_line_number_accounts_for_blank_lines(self):
        with self.assertRaises(AddressFormatError) as cm:
            parse_address("742 Main St\n\nChicago, IL")
        self.assertEqual(cm.exception.line, 3)

    def test_invalid_state_abbreviation(self):
        with self.assertRaises(AddressFormatError) as cm:
            parse_address("100 Main St\nChicago, ILL 60601")
        err = cm.exception
        self.assertEqual(err.line, 2)
        self.assertEqual(err.column, 10)
        self.assertIn("'ILL'", err.message)

    def test_unknown_two_letter_state_code(self):
        with self.assertRaises(AddressFormatError) as cm:
            parse_address("100 Main St\nChicago, ZZ 60601")
        self.assertIn("'ZZ'", cm.exception.message)

    def test_state_missing_entirely(self):
        with self.assertRaises(AddressFormatError) as cm:
            parse_address("100 Main St\n60601")
        err = cm.exception
        self.assertIn("expected a 2-letter state abbreviation", err.message)

    def test_missing_city(self):
        with self.assertRaises(AddressFormatError) as cm:
            parse_address("100 Main St\n, IL 62704")
        err = cm.exception
        self.assertEqual(err.line, 2)
        self.assertEqual(err.column, 1)
        self.assertIn("missing city", err.message)

    def test_error_str_has_caret_pointing_at_column(self):
        with self.assertRaises(AddressFormatError) as cm:
            parse_address("123 Main St\nChicago, IL")
        err = cm.exception
        lines = str(err).splitlines()
        self.assertEqual(lines[1], "    Chicago, IL")
        expected_pointer = " " * (err.column + 3) + "^"
        self.assertEqual(lines[2], expected_pointer)


if __name__ == "__main__":
    unittest.main()
