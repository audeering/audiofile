"""Read, write, and get information about audio files."""
from audiofile.core.info import bit_depth
from audiofile.core.info import channels
from audiofile.core.info import duration
from audiofile.core.info import samples
from audiofile.core.info import sampling_rate
from audiofile.core.io import convert_to_wav
from audiofile.core.io import read
from audiofile.core.io import write


# Discourage from audeer import *
__all__ = []


# Dynamically get the version of the installed module
try:
    import pkg_resources
    __version__ = pkg_resources.get_distribution(__name__).version
except Exception:  # pragma: no cover
    pkg_resources = None  # pragma: no cover
finally:
    del pkg_resources
