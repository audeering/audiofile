import os
import tempfile

import numpy as np
import soundfile

import audeer
import audmath

from audiofile.core.convert import convert
from audiofile.core.utils import MAX_CHANNELS
from audiofile.core.utils import SNDFORMATS
from audiofile.core.utils import duration_in_seconds
from audiofile.core.utils import file_extension


def _parse_time_value(
    value: float | int | str | np.timedelta64,
    sampling_rate: int,
) -> float | None:
    """Parse a time value (offset or duration) to seconds.

    Args:
        value: time value to parse
        sampling_rate: sampling rate for conversion

    Returns:
        time value in seconds, or None if NaN

    """
    if value is None:
        return None
    parsed = duration_in_seconds(value, sampling_rate)
    if np.isnan(parsed):
        return None
    return parsed


def _needs_sampling_rate(
    duration: float | int | str | np.timedelta64,
    offset: float | int | str | np.timedelta64,
) -> bool:
    """Check if sampling rate is needed for parsing offset/duration.

    Args:
        duration: duration value
        offset: offset value

    Returns:
        True if sampling rate is needed

    """
    if duration is not None or isinstance(duration, str):
        return True
    if offset is not None and isinstance(offset, str):
        return True
    if offset is not None and offset != 0:
        return True
    return False


def _normalize_offset_duration(
    offset: float | None,
    duration: float | None,
    signal_duration: float,
) -> tuple[float, float | None]:
    """Normalize offset and duration to handle negative values.

    Converts negative offset/duration values (counted from end)
    to positive values (counted from start).

    Args:
        offset: offset in seconds (can be negative or None)
        duration: duration in seconds (can be negative or None)
        signal_duration: total duration of signal in seconds

    Returns:
        tuple of (normalized_offset, normalized_duration)
        where offset is >= 0 and duration is >= 0 or None

    """
    # Handle: offset=None, duration < 0
    if offset is None and duration is not None and duration < 0:
        return max(0, signal_duration + duration), None

    # Handle: offset=None, duration >= 0
    if offset is None and duration is not None and duration >= 0:
        if np.isinf(duration):
            return 0, None
        return 0, duration

    # Guard: offset is None at this point means both are None
    if offset is None:
        return 0, None

    # Handle: offset >= 0, duration < 0
    if offset >= 0 and duration is not None and duration < 0:
        if np.isinf(offset) and np.isinf(duration):
            return 0, None
        if np.isinf(offset):
            return 0, 0.0
        if np.isinf(duration):
            offset = min(offset, signal_duration)
            duration = np.sign(duration) * signal_duration
        orig_offset = offset
        offset = max(0, offset + duration)
        duration = min(-duration, orig_offset)
        return offset, duration

    # Handle: offset >= 0, duration >= 0
    if offset >= 0 and duration is not None and duration >= 0:
        if np.isinf(offset):
            return 0, 0.0
        if np.isinf(duration):
            return offset, None
        return offset, duration

    # Handle: offset < 0, duration=None
    if offset < 0 and duration is None:
        return max(0, signal_duration + offset), None

    # Handle: offset >= 0, duration=None
    if offset >= 0 and duration is None:
        if np.isinf(offset):
            return 0, 0.0
        return offset, None

    # Handle: offset < 0, duration > 0
    if offset < 0 and duration is not None and duration > 0:
        if np.isinf(offset) and np.isinf(duration):
            return 0, None
        if np.isinf(offset):
            return 0, 0.0
        if np.isinf(duration):
            offset = signal_duration + offset
            offset = max(0, offset)
            return offset, None
        offset = signal_duration + offset
        if offset < 0:
            duration = max(0, duration + offset)
            offset = 0
        else:
            duration = min(duration, signal_duration - offset)
        return offset, duration

    # Handle: offset < 0, duration < 0
    if offset < 0 and duration < 0:
        if np.isinf(offset):
            return 0, 0.0
        if np.isinf(duration):
            duration = -signal_duration
        else:
            orig_offset = offset
            offset = max(0, signal_duration + offset + duration)
            duration = min(-duration, signal_duration + orig_offset)
            duration = max(0, duration)
        return offset, duration

    # Fallback (should not reach here)
    return offset if offset >= 0 else 0, duration


def _create_empty_signal(
    file: str,
    always_2d: bool,
) -> np.array:
    """Create an empty signal array with correct shape.

    Args:
        file: audio file path
        always_2d: if True, return 2D array even for mono

    Returns:
        empty numpy array with correct shape

    """
    from audiofile.core.info import channels as get_channels

    channels = get_channels(file)
    if channels > 1 or always_2d:
        return np.zeros((channels, 0))
    return np.zeros((0,))


def convert_to_wav(
    infile: str,
    outfile: str = None,
    offset: float | int | str | np.timedelta64 = None,
    duration: float | int | str | np.timedelta64 = None,
    bit_depth: int = 16,
    normalize: bool = False,
    overwrite: bool = False,
    **kwargs,
) -> str:
    """Convert any audio/video file to WAV.

    It uses soundfile for reading WAV, FLAC, MP3, OGG files,
    and sox or ffmpeg for reading all other files.
    If ``duration`` and/or ``offset`` are specified
    the resulting WAV file
    will be shortened accordingly.

    ``duration`` and ``offset``
    support all formats
    mentioned in :func:`audmath.duration_in_seconds`,
    like ``'2 ms'``, or ``pd.to_timedelta(2, 's')``.
    The exception is
    that float and integer values
    are always interpreted as seconds
    and strings without unit
    always as samples.
    If ``duration`` and/or ``offset`` are negative,
    they are interpreted from right to left,
    whereas ``duration`` starts from the end of the signal
    for ``offset=None``.
    If the signal is shorter than the requested ``duration`` and/or ``offset``
    only the part of the signal overlapping with the requested signal
    is returned,
    e.g. for a file containing the signal ``[0, 1, 2]``,
    ``duration=2``, ``offset=-4`` will return ``[0]``.

    ``duration`` and ``offset``
    are evenly rounded
    after conversion to samples.

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
        >>> path = audiofile.convert_to_wav("stereo.flac")
        >>> os.path.basename(path)
        'stereo.wav'

    """
    infile = audeer.safe_path(infile)
    if outfile is None:
        outfile = audeer.replace_file_extension(infile, "wav")
    else:
        outfile = audeer.safe_path(outfile)
    if infile == outfile and not overwrite:
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
    write(
        outfile,
        signal,
        sampling_rate,
        bit_depth=bit_depth,
        normalize=normalize,
        **kwargs,
    )
    return outfile


def read(
    file: str,
    duration: float | int | str | np.timedelta64 = None,
    offset: float | int | str | np.timedelta64 = None,
    always_2d: bool = False,
    dtype: str = "float32",
    **kwargs,
) -> tuple[np.array, int]:
    """Read audio file.

    It uses :func:`soundfile.read` for WAV, FLAC, MP3, and OGG files.
    All other audio files are
    first converted to WAV by sox or ffmpeg.

    ``duration`` and ``offset``
    support all formats
    mentioned in :func:`audmath.duration_in_seconds`,
    like ``'2 ms'``, or ``pd.to_timedelta(2, 's')``.
    The exception is
    that float and integer values
    are always interpreted as seconds
    and strings without unit
    always as samples.
    If ``duration`` and/or ``offset`` are negative,
    they are interpreted from right to left,
    whereas ``duration`` starts from the end of the signal
    for ``offset=None``.
    If the signal is shorter than the requested ``duration`` and/or ``offset``
    only the part of the signal overlapping with the requested signal
    is returned,
    e.g. for a file containing the signal ``[0, 1, 2]``,
    ``duration=2``, ``offset=-4`` will return ``[0]``.

    ``duration`` and ``offset``
    are evenly rounded
    after conversion to samples.

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
        .. plot::
            :context: reset
            :include-source: false

            import numpy as np
            from audiofile.core.io import read

        .. plot::
            :context: close-figs

            >>> signal, sampling_rate = audiofile.read("mono.wav", always_2d=True)
            >>> sampling_rate
            8000
            >>> signal.shape
            (1, 12000)
            >>> signal, sampling_rate = read("mono.wav")
            >>> signal.shape
            (12000,)
            >>> import audplot
            >>> audplot.waveform(signal)

        .. plot::
            :context: close-figs

            >>> signal, sampling_rate = audiofile.read("mono.wav", duration=0.5)
            >>> # Extend signal to original length
            >>> signal = np.pad(signal, (0, 8000))
            >>> audplot.waveform(signal)

        .. plot::
            :context: close-figs

            >>> signal, sampling_rate = audiofile.read("mono.wav", duration=-0.5)
            >>> # Extend signal to original length
            >>> signal = np.pad(signal, (8000, 0))
            >>> audplot.waveform(signal)

        .. plot::
            :context: close-figs

            >>> signal, sampling_rate = audiofile.read(
            ...     "mono.wav", offset="4000", duration="4000"
            ... )
            >>> # Extend signal to original length
            >>> signal = np.pad(signal, (4000, 4000))
            >>> audplot.waveform(signal)

        .. plot::
            :context: close-figs

            >>> # Use audresample for resampling and remixing
            >>> import audresample
            >>> signal, sampling_rate = audiofile.read("stereo.wav")
            >>> signal.shape
            (2, 12000)
            >>> target_rate = 16000
            >>> signal = audresample.resample(signal, sampling_rate, target_rate)
            >>> signal.shape
            (2, 24000)
            >>> signal = audresample.remix(signal, mixdown=True)
            >>> signal.shape
            (1, 24000)
            >>> audplot.waveform(signal)

    """  # noqa: E501
    file = audeer.safe_path(file)
    sampling_rate = None

    # Parse offset and duration values
    if _needs_sampling_rate(duration, offset):
        # Import sampling_rate here to avoid circular imports
        from audiofile.core.info import sampling_rate as get_sampling_rate

        sampling_rate = get_sampling_rate(file)

    duration = _parse_time_value(duration, sampling_rate)
    offset = _parse_time_value(offset, sampling_rate)

    # Normalize offset/duration values (handles negative values and infinity)
    needs_normalization = (offset is not None and (offset < 0 or np.isinf(offset))) or (
        duration is not None and (duration < 0 or np.isinf(duration))
    )
    if needs_normalization:
        # Import duration here to avoid circular imports
        from audiofile.core.info import duration as get_duration

        signal_duration = get_duration(file)
        offset, duration = _normalize_offset_duration(offset, duration, signal_duration)

    # Convert to samples and handle early return if duration == 0
    if duration is not None and duration != 0:
        duration = audmath.samples(duration, sampling_rate)
    if duration == 0:
        signal = _create_empty_signal(file, always_2d)
        return signal, sampling_rate

    if offset is not None and offset != 0:
        offset = audmath.samples(offset, sampling_rate)
    else:
        offset = 0

    tmpdir = None
    if file_extension(file) not in SNDFORMATS:
        # Convert file formats not recognized by soundfile to WAV first.
        #
        # NOTE: this is faster than loading them with librosa directly.
        # In addition, librosa seems to have an issue with the precision of
        # the returned magnitude
        # (https://github.com/librosa/librosa/issues/811).
        #
        with tempfile.TemporaryDirectory(prefix="audiofile") as tmpdir:
            tmpfile = os.path.join(tmpdir, "tmp.wav")
            # offset and duration have to be given in seconds
            if offset != 0:
                offset /= sampling_rate
            if duration is not None and duration != 0:
                duration /= sampling_rate
            if sampling_rate is None:
                # Infer sampling rate using mediainfo before conversion,
                # as ffmpeg does ignore the original sampling rate for opus files,
                # see:
                # * https://trac.ffmpeg.org/ticket/5240
                # * https://github.com/audeering/audiofile/issues/157
                from audiofile.core.info import sampling_rate as get_sampling_rate

                sampling_rate = get_sampling_rate(file)
            convert(file, tmpfile, offset, duration, sampling_rate)
            signal, sampling_rate = soundfile.read(
                tmpfile,
                dtype=dtype,
                always_2d=always_2d,
                **kwargs,
            )
    else:
        start = offset
        # duration == 0 is handled further above with immediate return
        if duration is not None:
            stop = duration + start
        else:
            stop = None
        signal, sampling_rate = soundfile.read(
            file,
            start=start,
            stop=stop,
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

    Save audio data provided as an array of shape ``(channels, samples)``
    or ``(samples,)``
    to a WAV, FLAC, NP3, or OGG file.
    ``channels`` can be up to 65535 for WAV,
    255 for OGG,
    2 for MP3,
    and 8 for FLAC.
    For monaural audio the array can be one-dimensional.

    It uses :func:`soundfile.write` to write the audio files.

    Args:
        file: file name of output audio file.
            The format (WAV, FLAC, MP3, OGG) will be inferred from the file name
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
        >>> audiofile.write("mono.wav", signal, sampling_rate)
        >>> signal = np.random.uniform(-1.2, 1.2, (2, 1000))
        >>> audiofile.write("stereo.flac", signal, sampling_rate, normalize=True)

    """  # noqa: E501
    file = audeer.safe_path(file)
    file_type = file_extension(file)

    # Check for allowed precisions
    if file_type == "wav":
        depth_mapping = {
            8: "PCM_U8",
            16: "PCM_16",
            24: "PCM_24",
            32: "PCM_32",
        }
    elif file_type == "flac":
        depth_mapping = {
            8: "PCM_S8",
            16: "PCM_16",
            24: "PCM_24",
        }
    if file_type in ["wav", "flac"]:
        bit_depths = sorted(list(depth_mapping.keys()))
        if bit_depth not in bit_depths:
            raise RuntimeError(
                f'"bit_depth" has to be one of '
                f"{', '.join([str(b) for b in bit_depths])}."
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
        if file_type != "wav":
            hint = " Consider using 'wav' instead."
        else:
            hint = ""
        raise RuntimeError(
            "The maximum number of allowed channels "
            f"for '{file_type}' is {MAX_CHANNELS[file_type]}.{hint}"
        )
    if normalize:
        signal = signal / np.max(np.abs(signal))
    soundfile.write(file, signal.T, sampling_rate, subtype=subtype, **kwargs)
