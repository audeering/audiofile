from doctest import ELLIPSIS
from doctest import NORMALIZE_WHITESPACE

import sybil
from sybil.parsers.rest import DocTestParser
from sybil.parsers.rest import PythonCodeBlockParser


# Collect doctests
#
# We use several `sybil.Sybil` instances
# to pass different fixtures for different files
#
parsers = [
    DocTestParser(optionflags=ELLIPSIS + NORMALIZE_WHITESPACE),
    PythonCodeBlockParser(),
]
pytest_collect_file = sybil.sybil.SybilCollection(
    (
        sybil.Sybil(
            parsers=parsers,
            filenames=[
                "usage.rst",
            ],
            fixtures=[
                "run_in_tmpdir",
            ],
        ),
    )
).pytest()
