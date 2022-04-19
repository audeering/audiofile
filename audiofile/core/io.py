import os
import tempfile
import typing

import numpy as np
import soundfile

import audeer

from audiofile.core.convert import convert
import audiofile.core.info as info
from audiofile.core.utils import (
    file_extension,
    MAX_CHANNELS,
    SNDFORMATS,
)


def convert_to_wav(
        infile: str,
        outfile: str,
        offset: float = 0,
        duration: float = None,
):
    """Convert any audio/video file to WAV.

    It uses soundfile for converting WAV, FLAC, OGG files,
    and sox or ffmpeg for converting all other files.
    If ``duration`` and/or ``offset`` are specified
    the resulting WAV file
    will be shortened accordingly.

    Args:
        infile: audio/video file name
        outfile: WAV file name
        duration: return only a specified duration in seconds
        offset: start reading at offset in seconds

    Raises:
        FileNotFoundError: if ffmpeg binary is needed,
            but cannot be found
        RuntimeError: if ``file`` is missing,
            broken or format is not supported

    """
    infile = audeer.safe_path(infile)
    outfile = audeer.safe_path(outfile)
    if file_extension(infile) in SNDFORMATS:
        bit_depth = info.bit_depth(infile)
        if bit_depth is None:
            bit_depth = 16
        signal, sampling_rate = read(
            infile,
            offset=offset,
            duration=duration,
        )
        write(outfile, signal, sampling_rate, bit_depth=bit_depth)
    else:
        convert(infile, outfile, offset, duration)


def read(
        file: str,
        duration: float = None,
        offset: float = 0,
        always_2d: bool = False,
        dtype: str = 'float32',
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
        always_2d: if ``True`` it always returns a two-dimensional signal
            even for mono sound files
        dtype: data type of returned signal,
            select from
            ``'float64'``,
            ``'float32'``,
            ``'int32'``,
            ``'int16'``
        kwargs: pass on further arguments to :func:`soundfile.read`

    Returns:
        * a two-dimensional array in the form
          ``[channels, samples]``.
          If the sound file has only one channel
          and ``always_2d=False``,
          a one-dimensional array is returned
        * sample rate of the audio file

    Raises:
        FileNotFoundError: if ffmpeg binary is needed,
            but cannot be found
        RuntimeError: if ``file`` is missing,
            broken or format is not supported

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
            convert(file, tmpfile, offset, duration)
            signal, sampling_rate = soundfile.read(
                tmpfile,
                dtype=dtype,
                always_2d=always_2d,
                **kwargs,
            )
    else:
        if duration is not None or offset > 0:
            sampling_rate = info.sampling_rate(file)
        if offset > 0:
            offset = np.ceil(offset * sampling_rate)  # samples
        if duration is not None:
            duration = int(
                np.ceil(duration * sampling_rate) + offset
            )  # samples
        signal, sampling_rate = soundfile.read(
            file,
            start=int(offset),
            stop=duration,
            dtype=dtype,
            always_2d=always_2d,
            **kwargs,
        )
    # [samples, channels] => [channels, samples]
    signal = signal.T
    return signal, sampling_rate


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

    Raises:
        RuntimeError: for non-supported bit depth or number of channels

    """
    file = audeer.safe_path(file)
    file_type = file_extension(file)

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
            raise RuntimeError(
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
            hint = " Consider using 'wav' instead."
        else:
            hint = ''
        raise RuntimeError(
            "The maximum number of allowed channels "
            f"for '{file_type}' is {MAX_CHANNELS[file_type]}.{hint}"
        )
    if normalize:
        signal = signal / np.max(np.abs(signal))
    soundfile.write(file, signal.T, sampling_rate, subtype=subtype, **kwargs)
