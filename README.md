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
optional and casing doesn't matter. Every line above it is treated as a
recipient/street line and passed through the same whitespace-collapsing,
title-casing normalisation.

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

## Known limitations (v1)

- US addresses only; no ZIP-to-state cross-check.
- Recipient and street lines aren't distinguished from each other, they're
  just normalised the same way.
- Title-casing is naive: it will turn "PO Box" into "Po Box" and "NW" into
  "Nw". Directionals and common abbreviations aren't special-cased yet.

## License

MIT, see `LICENSE`.
