import logging
import subprocess

import sox

import audeer

from audiofile.core.utils import (
    broken_file_error,
    run_ffmpeg,
    run_sox,
)


# Disable warning outputs of sox as we use it with try
logging.getLogger('sox').setLevel(logging.CRITICAL)


def convert_to_wav(
        infile: str,
        outfile: str,
        offset: float = 0,
        duration: float = None,
):
    """Convert any audio/video file to WAV.

    It uses sox or ffmpeg for the conversion.
    If ``duration`` and/or ``offset`` are specified
    the resulting WAV file
    will be shorter accordingly to those values.

    Args:
        infile: audio/video file name
        outfile: WAV file name
        duration: return only a specified duration in seconds
        offset: start reading at offset in seconds

    Raises:
        RuntimeError: if ``file`` is broken or not a supported format

    """
    infile = audeer.safe_path(infile)
    outfile = audeer.safe_path(outfile)
    try:
        # Convert to WAV file with sox
        run_sox(infile, outfile, offset, duration)
    except (sox.core.SoxError, sox.core.SoxiError):
        try:
            # Convert to WAV file with ffmpeg
            run_ffmpeg(infile, outfile, offset, duration)
        except subprocess.CalledProcessError:
            raise RuntimeError(broken_file_error(infile))
