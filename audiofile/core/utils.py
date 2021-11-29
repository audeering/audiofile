import os
import subprocess
import shlex

import sox

import audeer


def broken_file_error(file: str) -> str:
    r"""Broken file error message.

    If we encounter a broken file,
    we raise the same error for non SND files
    as soundfile does for SND files

    Args:
        file: file name

    Returns:
        error message

    """
    return (
        f'Error opening {file}: '
        'File contains data in an unknown format.'
    )


def file_extension(path):
    """Lower case file extension."""
    return audeer.file_extension(path).lower()


def run(shell_command):
    """Return the output of a shell command provided as string."""
    out = subprocess.check_output(
        shlex.split(shell_command),
        stderr=subprocess.STDOUT
    )
    try:
        return out.split()[0]
    except IndexError:
        return ''


def run_ffmpeg(infile, outfile, offset, duration):
    """Convert audio file to WAV file."""
    if duration:
        cmd = f'ffmpeg -ss {offset} -i "{infile}" -t {duration} "{outfile}"'
    else:
        cmd = f'ffmpeg -ss {offset} -i "{infile}" "{outfile}"'
    run(cmd)


def run_sox(infile, outfile, offset, duration):
    """Convert audio file to WAV file."""
    tfm = sox.Transformer()
    if duration:
        tfm.trim(offset, duration + offset)
    elif offset > 0:
        tfm.trim(offset)
    tfm.build(infile, outfile)


MAX_CHANNELS = {
    'wav': 65535,
    'ogg': 255,
    'flac': 8,
}
r"""Maximum number of channels per format."""

SNDFORMATS = ['wav', 'flac', 'ogg']
r"""File formats handled by soundfile"""
