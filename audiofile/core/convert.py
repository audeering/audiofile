import subprocess

from audiofile.core.utils import binary_missing_error
from audiofile.core.utils import broken_file_error
from audiofile.core.utils import run_ffmpeg
from audiofile.core.utils import run_sox


def convert(
    infile: str,
    outfile: str,
    offset: float = 0,
    duration: float = None,
    sampling_rate: int = None,
):
    """Convert any audio/video file to WAV.

    Args:
        infile: audio/video file name
        outfile: WAV file name
        duration: return only a specified duration in seconds
        offset: start reading at offset in seconds
        sampling_rate: sampling rate in Hz

    """
    try:
        # Convert to WAV file with sox
        run_sox(infile, outfile, offset, duration, sampling_rate)
    except (FileNotFoundError, subprocess.CalledProcessError):
        try:
            # Convert to WAV file with ffmpeg
            run_ffmpeg(infile, outfile, offset, duration, sampling_rate)
        except FileNotFoundError as e:  # pragma: no cover
            raise binary_missing_error("ffmpeg") from e
        except subprocess.CalledProcessError as e:  # pragma: no cover
            raise broken_file_error(infile) from e
