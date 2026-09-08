"""Error type for address parsing failures.

The whole point of this module is the __str__ output: a compiler-style
"line N, column N" message with the offending source line and a caret
pointing at the exact character that caused the problem.
"""


class AddressFormatError(ValueError):
    def __init__(self, message: str, line: int, column: int, source_line: str) -> None:
        self.message = message
        self.line = line
        self.column = column
        self.source_line = source_line
        super().__init__(message)

    def __str__(self) -> str:
        pointer = " " * (self.column - 1) + "^"
        return (
            f"line {self.line}, column {self.column}: {self.message}\n"
            f"    {self.source_line}\n"
            f"    {pointer}"
        )
