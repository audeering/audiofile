from doctest import ELLIPSIS
from doctest import NORMALIZE_WHITESPACE

from sybil import Sybil
from sybil.parsers.rest import DocTestParser
from sybil.parsers.rest import PythonCodeBlockParser

from audiofile.core.conftest import run_in_tmpdir  # noqa: F401


# Collect doctests
parsers = [
    DocTestParser(optionflags=ELLIPSIS | NORMALIZE_WHITESPACE),
    PythonCodeBlockParser(),
]
pytest_collect_file = Sybil(
    parsers=parsers,
    filenames=["usage.rst"],
    fixtures=["run_in_tmpdir"],
).pytest()
