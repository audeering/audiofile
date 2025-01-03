"""Read, write, and get information about audio files."""

from __future__ import annotations

import os
import subprocess
import tempfile

import soundfile

import audeer

from audiofile.core.io import convert_to_wav
from audiofile.core.utils import SNDFORMATS
from audiofile.core.utils import binary_missing_error
from audiofile.core.utils import broken_file_error
from audiofile.core.utils import file_extension
from audiofile.core.utils import run


def bit_depth(file: str) -> int | None:
    r"""Bit depth of audio file.

    For lossy audio files,
    ``None`` is returned as they have a varying bit depth.

    Args:
        file: file name of input audio file

    Returns:
        bit depth of audio file

    Raises:
        RuntimeError: if ``file`` is missing,
            broken or format is not supported

    Examples:
        >>> bit_depth("stereo.wav")
        16

    """
    file = audeer.safe_path(file)
    file_type = file_extension(file)
    if file_type == "wav":
        precision_mapping = {
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
    elif file_type == "flac":
        precision_mapping = {
            "PCM_16": 16,
            "PCM_24": 24,
            "PCM_32": 32,
            "PCM_S8": 8,
        }
    if file_extension(file) in ["wav", "flac"]:
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
        FileNotFoundError: if mediainfo binary is needed,
            but cannot be found
        RuntimeError: if ``file`` is missing,
            broken or format is not supported

    Examples:
        >>> channels("stereo.wav")
        2

    """
    file = audeer.safe_path(file)
    if file_extension(file) in SNDFORMATS:
        return soundfile.info(file).channels
    else:
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


def duration(file: str, sloppy=False) -> float:
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
        >>> duration("stereo.wav")
        1.5

    """
    file = audeer.safe_path(file)
    if file_extension(file) in SNDFORMATS:
        return soundfile.info(file).duration

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
        >>> has_video("stereo.wav")
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


def samples(file: str) -> int:
    """Number of samples in audio file.

    Audio files that are not WAV, FLAC, MP3, or OGG
    are first converted to WAV,
    before counting the samples.

    Args:
        file: file name of input audio file

    Returns:
        number of samples in audio file

    Raises:
        FileNotFoundError: if ffmpeg binary is needed,
            but cannot be found
        RuntimeError: if ``file`` is missing,
            broken or format is not supported

    Examples:
        >>> samples("stereo.wav")
        12000

    """

    def samples_as_int(file):
        return int(soundfile.info(file).duration * soundfile.info(file).samplerate)

    file = audeer.safe_path(file)
    if file_extension(file) in SNDFORMATS:
        return samples_as_int(file)
    else:
        # Always convert to WAV for non SNDFORMATS
        with tempfile.TemporaryDirectory(prefix="audiofile") as tmpdir:
            tmpfile = os.path.join(tmpdir, "tmp.wav")
            convert_to_wav(file, tmpfile)
            return samples_as_int(tmpfile)


def sampling_rate(file: str) -> int:
    """Sampling rate of audio file.

    Args:
        file: file name of input audio file

    Returns:
        sampling rate of audio file

    Raises:
        FileNotFoundError: if mediainfo binary is needed,
            but cannot be found
        RuntimeError: if ``file`` is missing,
            broken or format is not supported

    Examples:
        >>> sampling_rate("stereo.wav")
        8000

    """
    file = audeer.safe_path(file)
    if file_extension(file) in SNDFORMATS:
        return soundfile.info(file).samplerate
    else:
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
