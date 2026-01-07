"""Read, write, and get information about audio files."""

import io
import os
import subprocess
import tempfile

import soundfile

import audeer

from audiofile.core.io import convert_to_wav
from audiofile.core.utils import FILE_LIKE_UNSUPPORTED_ERROR
from audiofile.core.utils import SNDFORMATS
from audiofile.core.utils import binary_missing_error
from audiofile.core.utils import broken_file_error
from audiofile.core.utils import file_extension
from audiofile.core.utils import is_file_like
from audiofile.core.utils import run


def _normalize_file_input(file):
    """Normalize file input and detect file-like objects.

    Args:
        file: file path or file-like object

    Returns:
        tuple of (file, file_like, file_ext) where:
        - file: normalized path or original file-like object
        - file_like: True if file is a file-like object
        - file_ext: file extension (lowercase) or None

    """
    file_like = is_file_like(file)
    if not file_like:
        file = audeer.safe_path(file)
    file_ext = file_extension(file)
    return file, file_like, file_ext


def _sf_info(file, file_like):
    """Get soundfile info and reset seek position for file-like objects.

    Args:
        file: file path or file-like object
        file_like: True if file is a file-like object

    Returns:
        soundfile.info result

    """
    info = soundfile.info(file)
    if file_like:
        file.seek(0)
    return info


def _soundfile_supported(file_like, file_ext):
    """Check if file format is supported by soundfile for file-like objects.

    Args:
        file_like: True if file is a file-like object
        file_ext: file extension (lowercase) or None

    Returns:
        True if soundfile should be used

    Raises:
        RuntimeError: if file-like object has unsupported format

    """
    if file_ext in SNDFORMATS or (file_like and file_ext is None):
        return True
    if file_like:
        raise RuntimeError(FILE_LIKE_UNSUPPORTED_ERROR)
    return False


def bit_depth(file: str | io.IOBase) -> int | None:
    r"""Bit depth of audio file.

    For lossy audio files,
    ``None`` is returned as they have a varying bit depth.

    Args:
        file: file name of input audio file
            or file-like object

    Returns:
        bit depth of audio file

    Raises:
        RuntimeError: if ``file`` is missing,
            broken or format is not supported

    Examples:
        >>> audiofile.bit_depth("stereo.wav")
        16

    """
    file, file_like, file_type = _normalize_file_input(file)

    # For file-like objects without extension,
    # try to determine format from soundfile.info()
    if file_like and file_type is None:
        info = _sf_info(file, file_like)
        file_type = info.format.lower()

    # Raise error for unsupported file-like formats
    if file_like and file_type not in SNDFORMATS:
        raise RuntimeError(FILE_LIKE_UNSUPPORTED_ERROR)

    wav_precision_mapping = {
        "PCM_16": 16,
        "PCM_24": 24,
        "PCM_32": 32,
        "PCM_U8": 8,
        "FLOAT": 32,
        "DOUBLE": 64,
        "ULAW": 8,
        "ALAW": 8,
        "IMA_ADPCM": 4,
        "MS_ADPCM": 4,
        "GSM610": 16,  # not sure if this could be variable?
        "G721_32": 4,  # not sure if correct
    }
    flac_precision_mapping = {
        "PCM_16": 16,
        "PCM_24": 24,
        "PCM_32": 32,
        "PCM_S8": 8,
    }

    if file_type == "wav":
        info = _sf_info(file, file_like)
        depth = wav_precision_mapping[info.subtype]
    elif file_type == "flac":
        info = _sf_info(file, file_like)
        depth = flac_precision_mapping[info.subtype]
    else:
        depth = None

    return depth


def channels(file: str | io.IOBase) -> int:
    """Number of channels in audio file.

    Args:
        file: file name of input audio file
            or file-like object

    Returns:
        number of channels in audio file

    Raises:
        FileNotFoundError: if mediainfo binary is needed,
            but cannot be found
        RuntimeError: if ``file`` is missing,
            broken or format is not supported

    Examples:
        >>> audiofile.channels("stereo.wav")
        2

    """
    file, file_like, file_ext = _normalize_file_input(file)

    if _soundfile_supported(file_like, file_ext):
        info = _sf_info(file, file_like)
        return info.channels

    try:
        cmd = ["soxi", "-c", file]
        return int(run(cmd))
    except (FileNotFoundError, subprocess.CalledProcessError):
        # For MP4 stored and returned number of channels can be different
        cmd1 = ["mediainfo", "--Inform=Audio;%Channel(s)_Original%", file]
        cmd2 = ["mediainfo", "--Inform=Audio;%Channel(s)%", file]
        try:
            return int(run(cmd1))
        except FileNotFoundError:
            raise binary_missing_error("mediainfo")
        except (ValueError, subprocess.CalledProcessError):
            try:
                return int(run(cmd2))
            except (ValueError, subprocess.CalledProcessError):
                raise broken_file_error(file)


def duration(file: str | io.IOBase, sloppy=False) -> float:
    """Duration in seconds of audio file.

    The default behavior (``sloppy=False``)
    ensures
    the duration in seconds
    matches the one in samples.
    To achieve this it first decodes files to WAV
    if needed, e.g. MP4 files.
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
            or file-like object
        sloppy: if ``True`` report duration
            as stored in the header

    Returns:
        duration in seconds of audio file

    Raises:
        FileNotFoundError: if ffmpeg or mediainfo binary is needed,
            but cannot be found
        RuntimeError: if ``file`` is missing,
            broken or format is not supported

    Examples:
        >>> audiofile.duration("stereo.wav")
        1.5

    """
    file, file_like, file_ext = _normalize_file_input(file)

    if _soundfile_supported(file_like, file_ext):
        info = _sf_info(file, file_like)
        return info.duration

    if sloppy:
        try:
            cmd = ["soxi", "-D", file]
            duration = float(run(cmd))
        except (FileNotFoundError, subprocess.CalledProcessError):
            try:
                cmd = ["mediainfo", "--Inform=Audio;%Duration%", file]
                duration = run(cmd)
                if duration:
                    # Convert to seconds, as mediainfo returns milliseconds
                    duration = float(duration) / 1000
            except FileNotFoundError:
                raise binary_missing_error("mediainfo")
            # Behavior for broken files is different on Windows
            # where no error is raised,
            # but an empty duration is returned.
            # The error under Windows is then raised
            # when calling 'samples(file)'
            except subprocess.CalledProcessError:  # pragma: nocover
                raise broken_file_error(file)
        if duration:
            return duration

    return samples(file) / sampling_rate(file)


def has_video(file: str) -> bool:
    """If file contains video.

    For WAV, FLAC, MP3, or OGG files
    ``False`` is returned.
    All other files are probed by mediainfo.

    Args:
        file: file name of input file

    Returns:
        ``True`` if file contains video data

    Raises:
        FileNotFoundError: if mediainfo binary is needed,
            but cannot be found
        RuntimeError: if ``file`` is missing
            and does not end with ``"wav"``, ``"flac"``, ``"mp3"``, ``"ogg"``

    Examples:
        >>> audiofile.has_video("stereo.wav")
        False

    """
    if file_extension(file) in SNDFORMATS:
        return False
    else:
        try:
            path = audeer.path(file)
            if not os.path.exists(path):
                raise RuntimeError(f"'{file}' does not exist.")
            cmd = ["mediainfo", "--Inform=Video;%Format%", path]
            video_format = run(cmd)
            if len(video_format) > 0:
                return True
            else:
                return False
        except FileNotFoundError:
            raise binary_missing_error("mediainfo")


def samples(file: str | io.IOBase) -> int:
    """Number of samples in audio file.

    Audio files that are not WAV, FLAC, MP3, or OGG
    are first converted to WAV,
    before counting the samples.

    Args:
        file: file name of input audio file
            or file-like object

    Returns:
        number of samples in audio file

    Raises:
        FileNotFoundError: if ffmpeg binary is needed,
            but cannot be found
        RuntimeError: if ``file`` is missing,
            broken or format is not supported

    Examples:
        >>> audiofile.samples("stereo.wav")
        12000

    """

    def samples_as_int(file, file_like=False):
        info = _sf_info(file, file_like)
        return int(info.duration * info.samplerate)

    file, file_like, file_ext = _normalize_file_input(file)

    if _soundfile_supported(file_like, file_ext):
        return samples_as_int(file, file_like)

    # Always convert to WAV for non SNDFORMATS
    with tempfile.TemporaryDirectory(prefix="audiofile") as tmpdir:
        tmpfile = os.path.join(tmpdir, "tmp.wav")
        convert_to_wav(file, tmpfile)
        return samples_as_int(tmpfile)


def sampling_rate(file: str | io.IOBase) -> int:
    """Sampling rate of audio file.

    Args:
        file: file name of input audio file
            or file-like object

    Returns:
        sampling rate of audio file

    Raises:
        FileNotFoundError: if mediainfo binary is needed,
            but cannot be found
        RuntimeError: if ``file`` is missing,
            broken or format is not supported

    Examples:
        >>> audiofile.sampling_rate("stereo.wav")
        8000

    """
    file, file_like, file_ext = _normalize_file_input(file)

    if _soundfile_supported(file_like, file_ext):
        info = _sf_info(file, file_like)
        return info.samplerate

    try:
        cmd = ["soxi", "-r", file]
        return int(run(cmd))
    except (FileNotFoundError, subprocess.CalledProcessError):
        try:
            cmd = ["mediainfo", "--Inform=Audio;%SamplingRate%", file]
            sampling_rate = run(cmd)
            if sampling_rate:
                return int(sampling_rate)
            else:
                # Raise CalledProcessError
                # to align coverage under Windows and Linux
                raise subprocess.CalledProcessError(-2, cmd)
        except FileNotFoundError:
            raise binary_missing_error("mediainfo")
        except subprocess.CalledProcessError:
            raise broken_file_error(file)
