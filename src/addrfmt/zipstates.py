"""Map the first three digits of a ZIP code to the state(s) that use them.

USPS assigns ZIP codes in blocks by sectional center facility, so the
three-digit prefix is enough to catch a ZIP that belongs to a different
state than the one typed. It is not enough to prove a ZIP exists. Prefixes
that no state owns (military APO/FPO blocks, unassigned ranges) are left
out on purpose: for those we cannot say the ZIP is wrong, so no check is made.
"""

from typing import Dict, FrozenSet, Optional

# (first prefix, last prefix, states). A few prefixes are shared between
# territories and states, so the value is a tuple of codes.
_RANGES = (
    (5, 5, ("NY",)),
    (6, 7, ("PR",)),
    (8, 8, ("VI",)),
    (9, 9, ("PR",)),
    (10, 27, ("MA",)),
    (28, 29, ("RI",)),
    (30, 38, ("NH",)),
    (39, 49, ("ME",)),
    (50, 59, ("VT",)),
    (60, 69, ("CT",)),
    (70, 89, ("NJ",)),
    (100, 149, ("NY",)),
    (150, 196, ("PA",)),
    (197, 199, ("DE",)),
    (200, 200, ("DC",)),
    (201, 201, ("VA",)),
    (202, 205, ("DC",)),
    (206, 212, ("MD",)),
    (214, 219, ("MD",)),
    (220, 246, ("VA",)),
    (247, 268, ("WV",)),
    (270, 289, ("NC",)),
    (290, 299, ("SC",)),
    (300, 319, ("GA",)),
    (320, 339, ("FL",)),
    (341, 349, ("FL",)),
    (350, 369, ("AL",)),
    (370, 385, ("TN",)),
    (386, 397, ("MS",)),
    (398, 399, ("GA",)),
    (400, 427, ("KY",)),
    (430, 459, ("OH",)),
    (460, 479, ("IN",)),
    (480, 499, ("MI",)),
    (500, 528, ("IA",)),
    (530, 549, ("WI",)),
    (550, 567, ("MN",)),
    (569, 569, ("DC",)),
    (570, 577, ("SD",)),
    (580, 588, ("ND",)),
    (590, 599, ("MT",)),
    (600, 629, ("IL",)),
    (630, 658, ("MO",)),
    (660, 679, ("KS",)),
    (680, 693, ("NE",)),
    (700, 714, ("LA",)),
    (716, 729, ("AR",)),
    (730, 731, ("OK",)),
    (733, 733, ("TX",)),
    (734, 749, ("OK",)),
    (750, 799, ("TX",)),
    (800, 816, ("CO",)),
    (820, 831, ("WY",)),
    (832, 838, ("ID",)),
    (840, 847, ("UT",)),
    (850, 865, ("AZ",)),
    (870, 884, ("NM",)),
    (885, 885, ("TX",)),
    (889, 898, ("NV",)),
    (900, 961, ("CA",)),
    (967, 967, ("HI", "AS")),
    (968, 968, ("HI",)),
    (969, 969, ("GU", "MP")),
    (970, 979, ("OR",)),
    (980, 994, ("WA",)),
    (995, 999, ("AK",)),
)

_PREFIX_STATES: Dict[int, FrozenSet[str]] = {
    prefix: frozenset(states)
    for first, last, states in _RANGES
    for prefix in range(first, last + 1)
}


def states_for_zip(zip_code: str) -> Optional[FrozenSet[str]]:
    """Return the state codes that own this ZIP's prefix, or None if unknown."""
    return _PREFIX_STATES.get(int(zip_code[:3]))
