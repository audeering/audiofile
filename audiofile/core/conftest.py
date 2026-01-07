from doctest import ELLIPSIS
from doctest import NORMALIZE_WHITESPACE
import os

import numpy as np
import pytest
import sybil
from sybil.parsers.rest import DocTestParser

import audiofile


def imports(namespace):
    """Provide Python modules to namespace."""
    namespace["audiofile"] = audiofile


@pytest.fixture(scope="module")
def run_in_tmpdir(tmpdir_factory):
    """Move to a persistent tmpdir for execution of a whole file."""
    tmpdir = tmpdir_factory.mktemp("tmp")
    current_dir = os.getcwd()
    os.chdir(tmpdir)

    # Create test signals
    sampling_rate = 8000
    signal = np.random.uniform(-1, 1, (1, 1000))
    audiofile.write("mono.wav", signal, sampling_rate)
    signal = np.random.uniform(-1.2, 1.2, (2, 1000))
    audiofile.write("stereo.flac", signal, sampling_rate, normalize=True)
    audiofile.write("stereo.wav", signal, sampling_rate, normalize=True)

    yield

    os.chdir(current_dir)


# Collect doctests
pytest_collect_file = sybil.Sybil(
    parsers=[DocTestParser(optionflags=ELLIPSIS + NORMALIZE_WHITESPACE)],
    patterns=["*.py"],
    fixtures=[
        "run_in_tmpdir",
    ],
    setup=imports,
).pytest()
