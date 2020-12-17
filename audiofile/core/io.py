from __future__ import division
import os
import sys
import tempfile
import typing
import warnings

import numpy as np
import soundfile

import audeer

from audiofile.core.convert import convert_to_wav
from audiofile.core.info import sampling_rate
from audiofile.core.utils import (
    file_extension,
    MAX_CHANNELS,
    SNDFORMATS,
)


def read(
        file: str,
        duration: float = None,
        offset: float = 0,
        always_2d: bool = False,
        **kwargs,
) -> typing.Tuple[np.array, int]:
    """Read audio file.

    It uses :func:`soundfile.read` for WAV, FLAC, and OGG files.
    All other audio files are
    first converted to WAV by sox or ffmpeg.

    Args:
        file: file name of input audio file
        duration: return only a specified duration in seconds
        offset: start reading at offset in seconds
        always_2d: if `True` it always returns a two-dimensional signal
            even for mono sound files
        kwargs: pass on further arguments to :func:`soundfile.read`

    Returns:
        * a two-dimensional array in the form
          ``[channels, samples]``.
          If the sound file has only one channel,
          a one-dimensional array is returned
        * sample rate of the audio file

    Note:
        OGG file handling will not work properly under Ubuntu 16.04
        due to a bug in its libsndfile version.

    """
    file = audeer.safe_path(file)
    tmpdir = None
    if file_extension(file) not in SNDFORMATS:
        # Convert file formats not recognized by soundfile to WAV first.
        #
        # NOTE: this is faster than loading them with librosa directly.
        # In addition, librosa seems to have an issue with the precission of
        # the returned magnitude
        # (https://github.com/librosa/librosa/issues/811).
        #
        # It might be the case that MP3 files will be supported by soundfile in
        # the future as well. For a discussion on MP3 support in the underlying
        # libsndfile see https://github.com/erikd/libsndfile/issues/258.
        with tempfile.TemporaryDirectory(prefix='audiofile') as tmpdir:
            tmpfile = os.path.join(tmpdir, 'tmp.wav')
            convert_to_wav(file, tmpfile, offset, duration)
            signal, sample_rate = soundfile.read(
                tmpfile,
                dtype='float32',
                always_2d=always_2d,
                **kwargs,
            )
    else:
        if duration or offset > 0:
            sample_rate = sampling_rate(file)
        if offset > 0:
            offset = np.ceil(offset * sample_rate)  # samples
        if duration:
            duration = int(np.ceil(duration * sample_rate) + offset)  # samples
        signal, sample_rate = soundfile.read(
            file,
            start=int(offset),
            stop=duration,
            dtype='float32',
            always_2d=always_2d,
            **kwargs,
        )
    # [samples, channels] => [channels, samples]
    signal = signal.T
    return signal, sample_rate


def write(
        file: str,
        signal: np.array,
        sampling_rate: int,
        bit_depth: int = 16,
        normalize: bool = False,
        **kwargs,
):
    """Write (normalized) audio files.

    Save audio data provided as an array of shape ``[channels, samples]``
    to a WAV, FLAC, or OGG file.
    ``channels`` can be up to 65535 for WAV,
    255 for OGG,
    and 8 for FLAC.
    For monaural audio the array can be one-dimensional.

    It uses :func:`soundfile.write` to write the audio files.

    Args:
        file: file name of output audio file.
            The format (WAV, FLAC, OGG) will be inferred from the file name
        signal: audio data to write
        sampling_rate: sample rate of the audio data
        bit_depth: bit depth of written file in bit,
            can be 8, 16, 24 for WAV and FLAC files,
            and in addition 32 for WAV files
        normalize: normalize audio data before writing
        kwargs: pass on further arguments to :func:`soundfile.write`

    Note:
        OGG file handling does not work properly under Ubuntu 16.04
        due to a bug in its libsndfile version.

    """
    file = audeer.safe_path(file)
    file_type = file_extension(file)

    # Backward compatibility between bit_depth and precision
    backward_mapping = {
        '16bit': 16,
        '24bit': 24,
        '32bit': 32,
    }
    if bit_depth in backward_mapping.keys():
        warnings.warn(
            f'Use "{backward_mapping[bit_depth]}" instead of '
            f'"{bit_depth}" for specifying bit depth. '
            f'This will raise an error in version >=0.5.0'
        )
        bit_depth = backward_mapping[bit_depth]
    if 'precision' in kwargs.keys():
        _precision = kwargs.pop('precision')
        warnings.warn(
            f'Use "bit_depth={backward_mapping[_precision]}" '
            f'instead of "precision={_precision}" '
            f'for specifying bit depth. '
            f'This will raise an error in version >=0.5.0'
        )
        bit_depth = backward_mapping[_precision]

    # Check for allowed precisions
    if file_type == 'wav':
        depth_mapping = {
            8: 'PCM_U8',
            16: 'PCM_16',
            24: 'PCM_24',
            32: 'PCM_32',
        }
    elif file_type == 'flac':
        depth_mapping = {
            8: 'PCM_S8',
            16: 'PCM_16',
            24: 'PCM_24',
        }
    if file_type in ['wav', 'flac']:
        bit_depths = sorted(list(depth_mapping.keys()))
        if bit_depth not in bit_depths:
            sys.exit(
                f'"bit_depth" has to be one of '
                f'{", ".join([str(b) for b in bit_depths])}.'
            )
        subtype = depth_mapping[bit_depth]
    else:
        subtype = None
    # Check if number of channels is allowed for chosen file type
    if signal.ndim > 1:
        channels = np.shape(signal)[0]
    else:
        channels = 1
    if channels > MAX_CHANNELS[file_type]:
        if file_type != 'wav':
            hint = 'Consider using "wav" instead.'
        sys.exit(
            'The maximum number of allowed channels '
            f'for {file_type} is {MAX_CHANNELS[file_type]}. {hint}'
        )
    if normalize:
        signal = signal / np.max(np.abs(signal))
    soundfile.write(file, signal.T, sampling_rate, subtype=subtype, **kwargs)
