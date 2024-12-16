"""Read, write, and get information about audio files."""

from audiofile.core.info import bit_depth
from audiofile.core.info import channels
from audiofile.core.info import duration
from audiofile.core.info import has_video
from audiofile.core.info import samples
from audiofile.core.info import sampling_rate
from audiofile.core.io import convert_to_wav
from audiofile.core.io import read
from audiofile.core.io import write


# Discourage from audeer import *
__all__ = []


# Dynamically get the version of the installed module
try:
    import importlib.metadata

    __version__ = importlib.metadata.version(__name__)
except Exception:  # pragma: no cover
    importlib = None  # pragma: no cover
finally:
    del importlib
