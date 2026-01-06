import os
import subprocess

import numpy as np

import audmath


def is_file_like(obj) -> bool:
    r"""Check if object is a seekable file-like object.

    A file-like object is an object with ``read`` and ``seek`` methods,
    such as ``io.BytesIO``.

    Args:
        obj: object to check

    Returns:
        ``True`` if object is a seekable file-like object

    """
    return hasattr(obj, "read") and hasattr(obj, "seek")


MAX_CHANNELS = {
    "wav": 65535,
    "ogg": 255,
    "mp3": 2,
    "flac": 8,
}
r"""Maximum number of channels per format."""

SNDFORMATS = ["wav", "flac", "mp3", "ogg"]
r"""File formats handled by soundfile"""

FILE_LIKE_UNSUPPORTED_ERROR = (
    "File-like objects are only supported for WAV, FLAC, MP3, and OGG files."
)
r"""Error message for unsupported file-like formats."""


def binary_missing_error(binary: str) -> Exception:
    r"""Missing binary error message.

    Args:
        binary: name of binary

    Returns:
        error message

    """
    return FileNotFoundError(
        f"{binary} cannot be found.\n"
        "Please make sure it is installed.\n"
        "For further instructions visit: "
        "https://audeering.github.io/audiofile/installation.html"
    )


def broken_file_error(file: str) -> Exception:
    r"""Broken file error message.

    If we encounter a broken file,
    we raise the same error for non SND files
    as soundfile does for SND files

    Args:
        file: file name

    Returns:
        error message

    """
    return RuntimeError(
        f"Error opening {file}: File contains data in an unknown format."
    )


def duration_in_seconds(
    duration: float | int | str | np.timedelta64,
    sampling_rate: float | int,
) -> np.floating:
    r"""Duration in seconds.

    This mirrors the behavior of audmath.duration_in_seconds()
    but handles only string values without unit,
    e.g. ``'2000'`` as representing samples.

    """
    if isinstance(duration, str):
        duration = audmath.duration_in_seconds(duration, sampling_rate)
    else:
        duration = audmath.duration_in_seconds(duration)
    return duration


def file_extension(path):
    """Lower case file extension.

    For file-like objects,
    try to get the extension from the ``name`` attribute.
    Returns ``None`` if the extension cannot be determined.

    """
    # We are not using `audeer.file_extension()` here,
    # to save another call to `audeer.safe_path()`
    if is_file_like(path):
        if hasattr(path, "name") and path.name:
            return os.path.splitext(path.name)[-1][1:].lower()
        return None
    return os.path.splitext(path)[-1][1:].lower()


def run(shell_command):
    """Return the output of a shell command provided as string."""
    out = subprocess.check_output(shell_command, stderr=subprocess.STDOUT)
    try:
        return out.split()[0]
    except IndexError:
        return ""


def run_ffmpeg(infile, outfile, offset, duration, sampling_rate):
    """Convert audio file to WAV file."""
    cmd = ["ffmpeg", "-ss", str(offset), "-i", infile, outfile]
    if duration:
        cmd.insert(-1, "-t")
        cmd.insert(-1, str(duration))
    if sampling_rate:
        cmd.insert(-1, "-ar")
        cmd.insert(-1, str(sampling_rate))
    run(cmd)


def run_sox(infile, outfile, offset, duration, sampling_rate):
    """Convert audio file to WAV file."""
    cmd = ["sox", infile, outfile, "trim", str(offset)]
    if duration:
        cmd.append(str(duration))
    if sampling_rate:
        cmd += ["rate", str(sampling_rate)]
    run(cmd)
