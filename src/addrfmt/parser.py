"""Parse free-text US postal addresses into structured, normalised fields.

Input is treated as: zero or more non-blank lines of recipient/street
address, followed by a final non-blank line containing "city, state zip".
Blank lines are ignored for parsing purposes but still count towards line
numbers, so error positions match what the user sees in an editor.

The recipient/street lines are further split into ``recipient_lines`` and
``street_lines`` on ``ParsedAddress`` by looking for the first line that
starts with a house number or a PO box; everything above that is treated
as the recipient block.
"""

import re
from dataclasses import dataclass
from typing import Tuple

from .errors import AddressFormatError
from .zipstates import states_for_zip

# USPS two-letter codes: 50 states, DC, and the major territories.
US_STATE_CODES = frozenset(
    """
    AL AK AZ AR CA CO CT DE FL GA HI ID IL IN IA KS KY LA ME MD MA MI MN MS
    MO MT NE NV NH NJ NM NY NC ND OH OK OR PA RI SC SD TN TX UT VT VA WA WV
    WI WY DC PR VI GU AS MP
    """.split()
)

_ZIP_RE = re.compile(r"(?P<zip>\d{5}(?:-\d{4})?)\s*$")
_TRAILING_WORD_RE = re.compile(r"([A-Za-z][A-Za-z.]*)\s*,?\s*$")

# A line "looks like" the start of the street portion of the address if it
# opens with a house number or a PO box, since that's the one part of the
# address block recipient lines never look like.
_STREET_START_RE = re.compile(r"^\s*(\d|p\.?\s*o\.?\s*box\b)", re.IGNORECASE)

# Words that should stay all-caps instead of getting title-cased: postal
# directionals (as in "123 NW Elm St") and the PO Box abbreviation.
_UPPERCASE_WORDS = frozenset({"N", "S", "E", "W", "NE", "NW", "SE", "SW", "PO"})


def _split_recipient_and_street(entries: Tuple[str, ...]) -> Tuple[Tuple[str, ...], Tuple[str, ...]]:
    for i, line in enumerate(entries):
        if _STREET_START_RE.match(line):
            return entries[:i], entries[i:]
    # No line looked like a street start (e.g. a rural route or a format we
    # don't recognise). Fall back to treating the last line as the street,
    # since that's the line directly above city/state/zip.
    return entries[:-1], entries[-1:]


@dataclass(frozen=True)
class ParsedAddress:
    lines: Tuple[str, ...]
    recipient_lines: Tuple[str, ...]
    street_lines: Tuple[str, ...]
    city: str
    state: str
    zip_code: str

    def format(self) -> str:
        return "\n".join((*self.lines, f"{self.city}, {self.state} {self.zip_code}"))


def _titlecase_part(part: str) -> str:
    if not part:
        return part
    # Strip trailing punctuation before checking against the uppercase
    # word list, so "NW," and "PO." are recognised the same as "NW".
    core = part.rstrip(".,;:")
    trailing = part[len(core):]
    if core.upper() in _UPPERCASE_WORDS:
        return core.upper() + trailing
    return part[:1].upper() + part[1:].lower()


def _titlecase_word(word: str) -> str:
    # Title-case each hyphen-separated part so "winston-salem" becomes
    # "Winston-Salem" instead of "Winston-salem".
    parts = word.split("-")
    return "-".join(_titlecase_part(part) for part in parts)


def _normalise_text(text: str) -> str:
    collapsed = re.sub(r"\s+", " ", text).strip()
    return " ".join(_titlecase_word(word) for word in collapsed.split(" ") if word)


def parse_address(text: str) -> ParsedAddress:
    raw_lines = text.splitlines()
    numbered = [(i + 1, line) for i, line in enumerate(raw_lines) if line.strip()]

    if not numbered:
        raise AddressFormatError("input is empty", 1, 1, "")

    if len(numbered) < 2:
        lineno, line = numbered[0]
        raise AddressFormatError(
            "address needs at least one line before the city/state/ZIP line",
            lineno,
            1,
            line,
        )

    *street_entries, (last_lineno, last_line) = numbered

    zip_match = _ZIP_RE.search(last_line)
    if not zip_match:
        raise AddressFormatError(
            "expected a ZIP code (5 digits, optionally followed by -XXXX) "
            "at the end of this line",
            last_lineno,
            len(last_line) + 1,
            last_line,
        )
    zip_code = zip_match.group("zip")
    before_zip = last_line[: zip_match.start()]

    state_match = _TRAILING_WORD_RE.search(before_zip)
    if not state_match:
        raise AddressFormatError(
            "expected a 2-letter state abbreviation before the ZIP code",
            last_lineno,
            len(before_zip) + 1,
            last_line,
        )
    state_token = state_match.group(1)
    if len(state_token) != 2 or state_token.upper() not in US_STATE_CODES:
        raise AddressFormatError(
            f"expected a 2-letter state abbreviation (e.g. 'IL'), found {state_token!r}",
            last_lineno,
            state_match.start(1) + 1,
            last_line,
        )
    state_code = state_token.upper()

    owners = states_for_zip(zip_code)
    if owners is not None and state_code not in owners:
        expected = "/".join(sorted(owners))
        raise AddressFormatError(
            f"ZIP code {zip_code[:5]} belongs to {expected}, not {state_code}",
            last_lineno,
            zip_match.start("zip") + 1,
            last_line,
        )

    before_state = before_zip[: state_match.start()]
    city = before_state.strip(" ,\t")
    if not city:
        raise AddressFormatError(
            "missing city name before the state",
            last_lineno,
            1,
            last_line,
        )

    lines = tuple(_normalise_text(line) for _, line in street_entries)
    city = _normalise_text(city)

    recipient_lines, street_lines = _split_recipient_and_street(lines)

    return ParsedAddress(
        lines=lines,
        recipient_lines=recipient_lines,
        street_lines=street_lines,
        city=city,
        state=state_code,
        zip_code=zip_code,
    )


def format_address(text: str) -> str:
    return parse_address(text).format()
