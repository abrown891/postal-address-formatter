"""Command-line entry point.

Reads one address from stdin, prints the normalised form to stdout. On a
parse failure, prints the compiler-style error to stderr and exits 1, so
this behaves sensibly in a shell pipeline either way.
"""

import sys

from .errors import AddressFormatError
from .parser import format_address


def main() -> int:
    text = sys.stdin.read()
    try:
        formatted = format_address(text)
    except AddressFormatError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print(formatted)
    return 0


if __name__ == "__main__":
    sys.exit(main())
