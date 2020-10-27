"""Read, write, and get information about audio files."""
from __future__ import division
import logging
import os
import tempfile

import soundfile
import sox

from audiofile.core.convert import convert_to_wav
from audiofile.core.utils import (
    file_extension,
    run,
    SNDFORMATS,
)


# Disable warning outputs of sox as we use it with try
logging.getLogger('sox').setLevel(logging.CRITICAL)


def channels(file: str) -> int:
    """Number of channels in audio file.

    Args:
        file: file name of input audio file

    Returns:
        number of channels in audio file

    """
    if file_extension(file) in SNDFORMATS:
        return soundfile.info(file).channels
    else:
        try:
            return int(sox.file_info.channels(file))
        except sox.core.SoxiError:
            # For MP4 stored and returned number of channels can be different
            cmd1 = f'mediainfo --Inform="Audio;%Channel(s)_Original%" {file}'
            cmd2 = f'mediainfo --Inform="Audio;%Channel(s)%" {file}'
            try:
                return int(run(cmd1))
            except ValueError:
                return int(run(cmd2))


def duration(file: str) -> float:
    """Duration in seconds of audio file.

    Args:
        file: file name of input audio file

    Returns:
        duration in seconds of audio file

    """
    if file_extension(file) in SNDFORMATS:
        return soundfile.info(file).duration
    else:
        return samples(file) / sampling_rate(file)


def samples(file: str) -> int:
    """Number of samples in audio file (0 if unavailable).

    Args:
        file: file name of input audio file

    Returns:
        number of samples in audio file

    """
    def samples_as_int(file):
        return int(
            soundfile.info(file).duration * soundfile.info(file).samplerate
        )

    if file_extension(file) in SNDFORMATS:
        return samples_as_int(file)
    else:
        # Always convert to WAV for non SNDFORMATS
        with tempfile.TemporaryDirectory(prefix='audiofile') as tmpdir:
            tmpfile = os.path.join(tmpdir, 'tmp.wav')
            convert_to_wav(file, tmpfile)
            return samples_as_int(tmpfile)


def sampling_rate(file: str) -> int:
    """Sampling rate of audio file.

    Args:
        file: file name of input audio file

    Returns:
        sampling rate of audio file

    """
    if file_extension(file) in SNDFORMATS:
        return soundfile.info(file).samplerate
    else:
        try:
            return int(sox.file_info.sample_rate(file))
        except sox.core.SoxiError:
            cmd = f'mediainfo --Inform="Audio;%SamplingRate%" {file}'
            return int(run(cmd))
