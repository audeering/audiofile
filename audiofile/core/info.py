"""Read, write, and get information about audio files."""
import logging
import os
import tempfile
import typing

import soundfile
import sox

import audeer

from audiofile.core.convert import convert_to_wav
from audiofile.core.utils import (
    broken_file_error,
    file_extension,
    run,
    SNDFORMATS,
)


# Disable warning outputs of sox as we use it with try
logging.getLogger('sox').setLevel(logging.CRITICAL)


def bit_depth(file: str) -> typing.Optional[int]:
    r"""Bit depth of audio file.

    For lossy audio files,
    ``None`` is returned as they have a varying bit depth.

    Args:
        file: file name of input audio file

    Returns:
        bit depth of audio file

    Raises:
        RuntimeError: if ``file`` is broken or not a supported format

    """
    file = audeer.safe_path(file)
    file_type = file_extension(file)
    if file_type == 'wav':
        precision_mapping = {
            'PCM_16': 16,
            'PCM_24': 24,
            'PCM_32': 32,
            'PCM_U8': 8,
            'FLOAT': 32,
            'DOUBLE': 64,
            'ULAW': 8,
            'ALAW': 8,
            'IMA_ADPCM': 4,
            'MS_ADPCM': 4,
            'GSM610': 16,  # not sure if this could be variable?
            'G721_32': 4,  # not sure if correct
        }
    elif file_type == 'flac':
        precision_mapping = {
            'PCM_16': 16,
            'PCM_24': 24,
            'PCM_32': 32,
            'PCM_S8': 8,
        }
    if file_extension(file) in ['wav', 'flac']:
        depth = precision_mapping[soundfile.info(file).subtype]
    else:
        depth = None

    return depth


def channels(file: str) -> int:
    """Number of channels in audio file.

    Args:
        file: file name of input audio file

    Returns:
        number of channels in audio file

    Raises:
        RuntimeError: if ``file`` is broken or not a supported format

    """
    file = audeer.safe_path(file)
    if file_extension(file) in SNDFORMATS:
        return soundfile.info(file).channels
    else:
        try:
            return int(sox.file_info.channels(file))
        except sox.core.SoxiError:
            # For MP4 stored and returned number of channels can be different
            cmd1 = f'mediainfo --Inform="Audio;%Channel(s)_Original%" "{file}"'
            cmd2 = f'mediainfo --Inform="Audio;%Channel(s)%" "{file}"'
            try:
                return int(run(cmd1))
            except ValueError:
                try:
                    return int(run(cmd2))
                except ValueError:
                    raise RuntimeError(broken_file_error(file))


def duration(file: str, sloppy=False) -> float:
    """Duration in seconds of audio file.

    The default behavior (``sloppy=False``)
    ensures
    the duration in seconds
    matches the one in samples.
    To achieve this it first decodes files to WAV
    if needed, e.g. MP3 files.
    If you have different decoders
    on different machines,
    results might differ.

    The case ``sloppy=True`` returns the duration
    as reported in the header of the audio file.
    This is faster,
    but might still return different results
    on different machines
    as it depends on the installed software.
    If no duration information is provided in the header
    it will fall back to ``sloppy=False``.

    Args:
        file: file name of input audio file
        sloppy: if ``True`` report duration
            as stored in the header

    Returns:
        duration in seconds of audio file

    Raises:
        RuntimeError: if ``file`` is broken or not a supported format

    """
    file = audeer.safe_path(file)
    if file_extension(file) in SNDFORMATS:
        return soundfile.info(file).duration

    if sloppy:
        try:
            duration = sox.file_info.duration(file)
            if duration is None:
                duration = 0.0

            return duration
        except sox.core.SoxiError:
            cmd = f'mediainfo --Inform="Audio;%Duration%" "{file}"'
            duration = run(cmd)
            if duration:
                # Convert to seconds, as mediainfo returns milliseconds
                return float(duration) / 1000

    return samples(file) / sampling_rate(file)


def samples(file: str) -> int:
    """Number of samples in audio file.

    Args:
        file: file name of input audio file

    Returns:
        number of samples in audio file

    Raises:
        RuntimeError: if ``file`` is broken or not a supported format

    """
    def samples_as_int(file):
        return int(
            soundfile.info(file).duration * soundfile.info(file).samplerate
        )

    file = audeer.safe_path(file)
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

    Raises:
        RuntimeError: if ``file`` is broken or not a supported format

    """
    file = audeer.safe_path(file)
    if file_extension(file) in SNDFORMATS:
        return soundfile.info(file).samplerate
    else:
        try:
            return int(sox.file_info.sample_rate(file))
        except sox.core.SoxiError:
            cmd = f'mediainfo --Inform="Audio;%SamplingRate%" "{file}"'
            sampling_rate = run(cmd)
            if sampling_rate:
                return int(sampling_rate)
            else:
                raise RuntimeError(broken_file_error(file))
