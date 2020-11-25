import os
import subprocess
import shlex

import sox


def file_extension(path):
    """Lower case file extension."""
    return os.path.splitext(path)[-1][1:].lower()


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

PRECISIONG = {
    '8bit': 'PCM_S8',
    '16bit': 'PCM_16',
    '24bit': 'PCM_24',
    '32bit': 'PCM_32',
}
r"""Precision as returned by soundfile."""

SNDFORMATS = ['wav', 'flac', 'ogg']
r"""File formats handled by soundfile"""
