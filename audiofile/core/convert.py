import subprocess

from audiofile.core.utils import (
    binary_missing_error,
    broken_file_error,
    run_ffmpeg,
    run_sox,
)


def convert(
        infile: str,
        outfile: str,
        offset: float = 0,
        duration: float = None,
):
    """Convert any audio/video file to WAV.

    Args:
        infile: audio/video file name
        outfile: WAV file name
        duration: return only a specified duration in seconds
        offset: start reading at offset in seconds

    """
    try:
        # Convert to WAV file with sox
        run_sox(infile, outfile, offset, duration)
    except (FileNotFoundError, subprocess.CalledProcessError):
        try:
            # Convert to WAV file with ffmpeg
            run_ffmpeg(infile, outfile, offset, duration)
        except FileNotFoundError:
            raise binary_missing_error('ffmpeg')
        except subprocess.CalledProcessError:
            raise broken_file_error(infile)
