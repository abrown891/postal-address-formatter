# addrfmt

A small library for turning messy, free-typed US postal addresses into a
consistent form:

```
742 Evergreen Terrace
Springfield, IL 62704-1234
```

Addresses show up in forms, spreadsheets, and imported CSVs in all kinds of
shapes: missing commas, lowercase everything, tabs instead of spaces, the
state spelled out instead of abbreviated. `addrfmt` parses that mess into
structured fields and re-renders it consistently. When it can't, it tells you
exactly where the input broke, not just that it did.

## Install

No dependencies, no PyPI package yet. Vendor `src/addrfmt` into your project
or add this repo as a path dependency.

## Usage

```python
from addrfmt import format_address

address = """Jane Doe
742 evergreen terrace
springfield il 62704-1234"""

print(format_address(address))
```

```
Jane Doe
742 Evergreen Terrace
Springfield, IL 62704-1234
```

The last non-blank line is always treated as `city, state zip`; the comma is
optional and casing doesn't matter. Every line above it is passed through
the same whitespace-collapsing, title-casing normalisation and is available
as `parsed.lines`.

`ParsedAddress` also splits those lines into `recipient_lines` and
`street_lines`, by looking for the first line that starts with a house
number or a PO box:

```python
from addrfmt import parse_address

parsed = parse_address("Jane Doe\n742 Evergreen Terrace\nSpringfield IL 62704")
parsed.recipient_lines  # ("Jane Doe",)
parsed.street_lines     # ("742 Evergreen Terrace",)
```

If no line looks like a street start, the last line before city/state/zip
is assumed to be the street line.

## Errors with real coordinates

This is the part I actually care about. When parsing fails, the exception
carries the line and column of the problem, plus a caret pointing at it,
the same way a compiler would report a syntax error:

```python
from addrfmt import format_address, AddressFormatError

bad = """Jane Doe
742 Evergreen Terrace
Springfield, Illinois 62704"""

try:
    format_address(bad)
except AddressFormatError as e:
    print(e)
```

```
line 3, column 14: expected a 2-letter state abbreviation (e.g. 'IL'), found 'Illinois'
    Springfield, Illinois 62704
                 ^
```

`AddressFormatError` also exposes `.line`, `.column`, `.message`, and
`.source_line` separately, so callers building a UI around this (a form
validator, say) can highlight the exact span instead of parsing the string
message.

## Command line

Installing the package (`pip install .` from a checkout, or `pip install -e .`
for development) also gives you an `addrfmt` command that reads one address
from stdin and prints the normalised form:

```
$ printf 'Jane Doe\n742 evergreen terrace\nspringfield il 62704-1234\n' | addrfmt
Jane Doe
742 Evergreen Terrace
Springfield, IL 62704-1234
```

On a parse failure it prints the same "line N, column N" error to stderr and
exits with status 1, so it's safe to use in a pipeline. `python -m addrfmt`
works the same way without installing the console script.

## Known limitations (v1)

- US addresses only.
- The ZIP is checked against the state by its first three digits, and a
  mismatch is reported at the ZIP's column. This catches a wrong state, not
  a ZIP that doesn't exist, and prefixes no state owns (military APO/FPO)
  are not checked.
- Recipient/street line splitting is a heuristic (first line starting with
  a house number or PO box); unusual formats like rural routes can guess
  wrong.
- Title-casing special-cases compass directionals (N, S, E, W, NE, NW, SE,
  SW) and "PO" so they stay upper-case, but other street abbreviations
  ("St", "Ave", "Blvd") are still just title-cased like any other word.

## License

MIT, see `LICENSE`.
