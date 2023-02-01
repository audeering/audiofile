import os
import tempfile
import typing

import numpy as np
import soundfile

import audeer

from audiofile.core.convert import convert
from audiofile.core.utils import (
    duration_in_seconds,
    file_extension,
    MAX_CHANNELS,
    SNDFORMATS,
)
from audiofile.core.utils import sampling_rate as get_sampling_rate


def convert_to_wav(
        infile: str,
        outfile: str = None,
        offset: typing.Union[float, int, str, np.timedelta64] = 0,
        duration: typing.Union[float, int, str, np.timedelta64] = None,
        bit_depth: int = 16,
        normalize: bool = False,
        overwrite: bool = False,
        **kwargs,
) -> str:
    """Convert any audio/video file to WAV.

    It uses soundfile for reading WAV, FLAC, OGG files,
    and sox or ffmpeg for reading all other files.
    If ``duration`` and/or ``offset`` are specified
    the resulting WAV file
    will be shortened accordingly.

    The duration values ``duration`` and ``offset``
    are expected to be given in seconds,
    but they support all formats
    mentioned in :func:`audmath.duration_in_seconds`
    with the exception of samples,
    which can only be given as a string,
    e.g. ``'200'``.

    It then uses :func:`soundfile.write` to write the WAV file,
    which limits the number of supported channels to 65535.

    Args:
        infile: audio/video file name
        outfile: WAV file name.
            If ``None`` same path as ``infile``
            but file extension is replaced by ``'wav'``
        duration: return only a specified duration
        offset: start reading at offset
        bit_depth: bit depth of written file in bit,
            can be 8, 16, 24
        normalize: normalize audio data before writing
        overwrite: force overwriting
            if ``outfile`` is identical to ``outfile``
        kwargs: pass on further arguments to :func:`soundfile.write`

    Returns:
        absolute path to resulting WAV file

    Raises:
        FileNotFoundError: if ffmpeg binary is needed,
            but cannot be found
        RuntimeError: if ``file`` is missing,
            broken or format is not supported
        RuntimeError: if ``infile`` would need to be overwritten
            and ``overwrite`` is ``False``
        ValueError: if ``duration`` is a string
            that does not match a valid '<value><unit>' pattern
            or the provided unit is not supported

    Examples:
        >>> path = convert_to_wav('stereo.flac')
        >>> os.path.basename(path)
        'stereo.wav'

    """
    infile = audeer.safe_path(infile)
    if outfile is None:
        outfile = audeer.replace_file_extension(infile, 'wav')
    else:
        outfile = audeer.safe_path(outfile)
    if (
            infile == outfile
            and not overwrite
    ):
        raise RuntimeError(
            f"'{infile}' would be overwritten. "
            "Select 'overwrite=True', "
            "or provide an 'outfile' argument."
        )
    signal, sampling_rate = read(
        infile,
        offset=offset,
        duration=duration,
    )
    write(outfile, signal, sampling_rate, bit_depth=bit_depth, **kwargs)
    return outfile


def read(
        file: str,
        duration: typing.Union[float, int, str, np.timedelta64] = None,
        offset: typing.Union[float, int, str, np.timedelta64] = 0,
        always_2d: bool = False,
        dtype: str = 'float32',
        **kwargs,
) -> typing.Tuple[np.array, int]:
    """Read audio file.

    It uses :func:`soundfile.read` for WAV, FLAC, and OGG files.
    All other audio files are
    first converted to WAV by sox or ffmpeg.

    The duration values ``duration`` and ``offset``
    are expected to be given in seconds,
    but they support all formats
    mentioned in :func:`audmath.duration_in_seconds`
    with the exception of samples,
    which can only be given as a string,
    e.g. ``'200'``.

    Args:
        file: file name of input audio file
        duration: return only the specified duration
        offset: start reading at offset
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
        ValueError: if ``duration`` is a string
            that does not match a valid '<value><unit>' pattern
            or the provided unit is not supported

    Examples:
        >>> signal, sampling_rate = read('mono.wav')
        >>> sampling_rate
        8000
        >>> signal.shape
        (1000,)
        >>> signal, sampling_rate = read('mono.wav', always_2d=True)
        >>> signal.shape
        (1, 1000)
        >>> signal, sampling_rate = read('stereo.wav', duration=0.1)
        >>> signal.shape
        (2, 800)
        >>> signal, sampling_rate = read('stereo.wav', duration='400')
        >>> signal.shape
        (2, 400)
        >>> # Use audresample for resampling and remixing
        >>> import audresample
        >>> target_rate = 16000
        >>> signal = audresample.resample(signal, sampling_rate, target_rate)
        >>> signal.shape
        (2, 1600)
        >>> signal = audresample.remix(signal, mixdown=True)
        >>> signal.shape
        (1, 1600)

    """
    file = audeer.safe_path(file)

    if duration is not None or offset != 0:
        sampling_rate = get_sampling_rate(file)
    if duration is not None:
        duration = duration_in_seconds(duration, sampling_rate)
    if offset != 0:
        offset = duration_in_seconds(offset, sampling_rate)

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

    Examples:
        >>> sampling_rate = 8000
        >>> signal = np.random.uniform(-1, 1, (1, 1000))
        >>> write('mono.wav', signal, sampling_rate)
        >>> signal = np.random.uniform(-1.2, 1.2, (2, 1000))
        >>> write('stereo.flac', signal, sampling_rate, normalize=True)

    """  # noqa: E501
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
