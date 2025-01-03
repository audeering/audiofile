import os
import re

import numpy as np
from numpy.testing import assert_allclose
import pandas as pd
import pytest
import soundfile

import audeer

import audiofile as af


SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
ASSETS_DIR = os.path.join(SCRIPT_DIR, "assets")


@pytest.fixture(scope="module")
def audio_file(tmpdir_factory, request):
    """Fixture to generate audio file.

    Provide ``(signal, sampling_rate)``
    as parameter to this fixture.

    """
    file = str(tmpdir_factory.mktemp("audio").join("file.wav"))
    signal, sampling_rate = request.param
    af.write(file, signal, sampling_rate)

    yield file


@pytest.fixture(scope="function")
def empty_file(tmpdir, request):
    """Fixture to generate empty audio files.

    The request parameter allows to select the file extension.

    """
    # Create empty audio file
    empty_file = os.path.join(tmpdir, "empty-file.wav")
    af.write(empty_file, np.array([[]]), 16000)

    # Rename to match extension
    file_ext = request.param
    ofpath = audeer.replace_file_extension(empty_file, file_ext)
    if os.path.exists(empty_file):
        os.rename(empty_file, ofpath)

    yield ofpath

    if os.path.exists(ofpath):
        os.remove(ofpath)


@pytest.fixture(scope="function")
def hide_system_path():
    """Fixture to hide system path in test."""
    current_path = os.environ["PATH"]
    os.environ["PATH"] = ""

    yield

    os.environ["PATH"] = current_path


@pytest.fixture(scope="function")
def non_audio_file(tmpdir, request):
    """Fixture to generate broken audio files.

    The request parameter allows to select the file extension.

    """
    # Create empty file to simulate broken/non-audio file
    file_ext = request.param
    broken_file = os.path.join(tmpdir, f"broken-file.{file_ext}")
    open(broken_file, "w").close()

    yield broken_file

    if os.path.exists(broken_file):
        os.remove(broken_file)


def tolerance(condition, sampling_rate=0):
    """Absolute tolerance for different condition."""
    tol = 0
    if condition == 8:
        tol = 2**-7
    elif condition == 16:
        tol = 2**-11  # half precision
    elif condition == 24:
        tol = 2**-17  # to be checked
    elif condition == 32:
        tol = 2**-24  # single precision
    elif condition == "duration":
        tol = 1 / sampling_rate
    return tol


def ensure_two_dimensions(x):
    """Converts (n,) to (1, n)."""
    return np.atleast_2d(x)


def sine(duration=1, sampling_rate=44100, channels=1, magnitude=1, frequency=100):
    """Generate test tone."""
    t = np.linspace(0, duration, int(np.ceil(duration * sampling_rate)))
    signal = magnitude * np.sin(2 * np.pi * frequency * t)
    if channels > 1:
        signal = ensure_two_dimensions(signal)
        signal = np.repeat(signal, channels, axis=0)
    return signal


def write_and_read(
    file,
    signal,
    sampling_rate,
    bit_depth=16,
    always_2d=False,
    normalize=False,
):
    """Write and read audio files."""
    af.write(file, signal, sampling_rate, bit_depth, normalize)
    return af.read(file, always_2d=always_2d)


def _channels(signal):
    signal = ensure_two_dimensions(signal)
    return np.shape(signal)[0]


def _samples(signal):
    signal = ensure_two_dimensions(signal)
    return np.shape(signal)[1]


def _duration(signal, sampling_rate):
    return _samples(signal) / sampling_rate


def _magnitude(signal):
    return np.max(np.abs(signal))


@pytest.mark.parametrize("duration", ["0", 0, 0.0])
@pytest.mark.parametrize("offset", [0, 1])
def test_read(tmpdir, duration, offset):
    file = str(tmpdir.join("signal.wav"))
    sampling_rate = 8000
    signal = sine(
        duration=0.1,
        sampling_rate=sampling_rate,
        channels=1,
    )
    af.write(file, signal, sampling_rate)
    sig, fs = af.read(file, duration=duration, offset=offset)
    assert sig.shape == (0,)
    assert fs == sampling_rate
    sig, fs = af.read(file, always_2d=True, duration=duration, offset=offset)
    assert sig.shape == (1, 0)
    assert fs == sampling_rate


@pytest.mark.parametrize(
    "convert",
    (True, False),
)
@pytest.mark.parametrize(
    "empty_file",
    ("bin", "mp4", "wav"),
    indirect=True,
)
def test_empty_file(tmpdir, convert, empty_file):
    if convert:
        converted_file = str(tmpdir.join("signal-converted.wav"))
        path = af.convert_to_wav(empty_file, converted_file)
        assert path == audeer.path(converted_file)
        empty_file = converted_file
    # Reading file
    signal, sampling_rate = af.read(empty_file)
    assert len(signal) == 0
    # Metadata
    for sloppy in [True, False]:
        assert af.duration(empty_file, sloppy=sloppy) == 0.0
    assert af.channels(empty_file) == 1
    assert af.sampling_rate(empty_file) == sampling_rate
    assert af.samples(empty_file) == 0
    if audeer.file_extension(empty_file) == "wav":
        assert af.bit_depth(empty_file) == 16
    else:
        assert af.bit_depth(empty_file) is None


@pytest.mark.parametrize(
    "empty_file",
    ("bin", "mp4"),
    indirect=True,
)
def test_missing_binaries(tmpdir, hide_system_path, empty_file):
    expected_error = FileNotFoundError
    # Reading file
    with pytest.raises(expected_error, match="mediainfo"):
        signal, sampling_rate = af.read(empty_file)
    # Metadata
    with pytest.raises(expected_error, match="mediainfo"):
        af.channels(empty_file)
    with pytest.raises(expected_error, match="mediainfo"):
        af.duration(empty_file)
    with pytest.raises(expected_error, match="mediainfo"):
        af.duration(empty_file, sloppy=True)
    with pytest.raises(expected_error, match="mediainfo"):
        af.has_video(empty_file)
    with pytest.raises(expected_error, match="mediainfo"):
        af.samples(empty_file)
    with pytest.raises(expected_error, match="mediainfo"):
        af.sampling_rate(empty_file)

    # Convert
    with pytest.raises(expected_error, match="mediainfo"):
        converted_file = str(tmpdir.join("signal-converted.wav"))
        af.convert_to_wav(empty_file, converted_file)


@pytest.mark.parametrize(
    "ext",
    ("bin", "mp4", "wav"),
)
def test_missing_file(tmpdir, ext):
    missing_file = f"missing_file.{ext}"
    expected_error = RuntimeError
    # Reading file
    with pytest.raises(expected_error):
        signal, sampling_rate = af.read(missing_file)
    # Metadata
    with pytest.raises(expected_error):
        af.sampling_rate(missing_file)
    with pytest.raises(expected_error):
        af.channels(missing_file)
    with pytest.raises(expected_error):
        af.duration(missing_file)
    with pytest.raises(expected_error):
        af.duration(missing_file, sloppy=True)
    # Convert
    with pytest.raises(expected_error):
        converted_file = str(tmpdir.join("signal-converted.wav"))
        af.convert_to_wav(missing_file, converted_file)


@pytest.mark.parametrize(
    "file, expected_error, expected_error_message",
    [
        ("missing_file.bin", RuntimeError, "'missing_file.bin' does not exist"),
        ("missing_file.mp4", RuntimeError, "'missing_file.mp4' does not exist"),
        ("missing_file.wav", None, None),
    ],
)
def test_missing_file_has_video(file, expected_error, expected_error_message):
    if expected_error is not None:
        with pytest.raises(expected_error, match=expected_error_message):
            af.has_video(file)
    else:
        assert af.has_video(file) is False


@pytest.mark.parametrize(
    "non_audio_file",
    ("bin", "mp4", "wav"),
    indirect=True,
)
def test_broken_file(tmpdir, non_audio_file):
    # Only match the beginning of error message
    # as the default soundfile message differs at the end on macOS
    error_msg = "Error opening"
    expected_error = RuntimeError
    # Reading file
    with pytest.raises(expected_error, match=error_msg):
        af.read(non_audio_file)
    # Metadata
    if audeer.file_extension(non_audio_file) == "wav":
        with pytest.raises(expected_error, match=error_msg):
            af.bit_depth(non_audio_file)
    else:
        assert af.bit_depth(non_audio_file) is None
    with pytest.raises(expected_error, match=error_msg):
        af.channels(non_audio_file)
    with pytest.raises(expected_error, match=error_msg):
        af.duration(non_audio_file)
    with pytest.raises(expected_error, match=error_msg):
        af.duration(non_audio_file, sloppy=True)
    with pytest.raises(expected_error, match=error_msg):
        af.samples(non_audio_file)
    with pytest.raises(expected_error, match=error_msg):
        af.sampling_rate(non_audio_file)
    # Convert
    with pytest.raises(expected_error, match=error_msg):
        converted_file = str(tmpdir.join("signal-converted.wav"))
        af.convert_to_wav(non_audio_file, converted_file)


@pytest.mark.parametrize("normalize", [False, True])
@pytest.mark.parametrize("bit_depth", [8, 16, 24])
@pytest.mark.parametrize(
    "file_extension",
    ("wav", "flac", "ogg", "mp3"),
)
def test_convert_to_wav(tmpdir, normalize, bit_depth, file_extension):
    sampling_rate = 8000
    channels = 1
    magnitude_offset = 0.5
    signal = sine(
        duration=0.1,
        magnitude=1 - magnitude_offset,
        sampling_rate=sampling_rate,
        channels=channels,
    )
    infile = str(tmpdir.join(f"signal.{file_extension}"))
    af.write(infile, signal, sampling_rate, bit_depth=bit_depth)
    if file_extension == "wav":
        error_msg = (
            f"'{infile}' would be overwritten. "
            "Select 'overwrite=True', "
            "or provide an 'outfile' argument."
        )
        with pytest.raises(RuntimeError, match=re.escape(error_msg)):
            outfile = af.convert_to_wav(
                infile,
                bit_depth=bit_depth,
                normalize=normalize,
            )
        outfile = af.convert_to_wav(
            infile,
            bit_depth=bit_depth,
            normalize=normalize,
            overwrite=True,
        )
    else:
        outfile = str(tmpdir.join("signal_converted.wav"))
        af.convert_to_wav(
            infile,
            outfile,
            bit_depth=bit_depth,
            normalize=normalize,
        )
    converted_signal, converted_sampling_rate = af.read(outfile)
    assert converted_sampling_rate == sampling_rate
    if normalize:
        # The actual maximum/minimum value can vary
        # based on the used codec/format
        assert converted_signal.max() > 0.95
        assert converted_signal.max() <= 1.0
        assert converted_signal.min() < -0.95
        assert converted_signal.min() >= -1.0
    if file_extension == "mp3":
        assert af.bit_depth(outfile) == bit_depth
        # Don't compare signals for MP3
        # as duration differs as well
    else:
        abs_difference = np.abs(converted_signal - signal).max()
    if file_extension == "ogg":
        assert af.bit_depth(outfile) == bit_depth
        if normalize:
            assert abs_difference < 0.06 + magnitude_offset
        else:
            assert abs_difference < 0.06
    elif file_extension in ["wav", "flac"]:
        assert af.bit_depth(outfile) == bit_depth
        if normalize:
            assert abs_difference < tolerance(bit_depth) + magnitude_offset
        else:
            assert abs_difference < tolerance(bit_depth)


@pytest.mark.parametrize("bit_depth", [8, 16, 24, 32])
@pytest.mark.parametrize("duration", [0.01, 0.9999, 2])
@pytest.mark.parametrize("sampling_rate", [100, 8000, 44100])
@pytest.mark.parametrize("channels", [1, 2, 3, 10])
@pytest.mark.parametrize("always_2d", [False, True])
def test_wav(tmpdir, bit_depth, duration, sampling_rate, channels, always_2d):
    file = str(tmpdir.join("signal.wav"))
    signal = sine(duration=duration, sampling_rate=sampling_rate, channels=channels)
    sig, fs = write_and_read(
        file,
        signal,
        sampling_rate,
        bit_depth=bit_depth,
        always_2d=always_2d,
    )
    # Expected number of samples
    samples = int(np.ceil(duration * sampling_rate))
    # Compare with soundfile implementation to check write()
    info = soundfile.info(file)
    assert_allclose(
        info.duration,
        duration,
        rtol=0,
        atol=tolerance("duration", sampling_rate),
    )
    assert info.samplerate == sampling_rate
    assert info.channels == channels
    assert info.frames == samples
    # Compare with signal values to check read()
    assert_allclose(
        _duration(sig, fs),
        duration,
        rtol=0,
        atol=tolerance("duration", sampling_rate),
    )
    assert fs == sampling_rate
    assert _channels(sig) == channels
    assert _samples(sig) == samples
    # Test audiofile metadata methods
    assert_allclose(
        af.duration(file), duration, rtol=0, atol=tolerance("duration", sampling_rate)
    )
    assert af.sampling_rate(file) == sampling_rate
    assert af.channels(file) == channels
    assert af.samples(file) == samples
    assert af.bit_depth(file) == bit_depth
    # Test types of audiofile metadata methods
    assert isinstance(af.duration(file), float)
    assert isinstance(af.sampling_rate(file), int)
    assert isinstance(af.channels(file), int)
    assert isinstance(af.samples(file), int)
    # Test dimensions of array
    if channels == 1 and not always_2d:
        assert sig.ndim == 1
    else:
        assert sig.ndim == 2

    # Test additional arguments to read
    if sampling_rate > 100:
        offset = 0.001
        duration = duration - 2 * offset
        sig, fs = af.read(
            file,
            offset=offset,
            duration=duration,
            always_2d=always_2d,
        )
        assert _samples(sig) == round(duration * sampling_rate)


@pytest.mark.parametrize("magnitude", [0.01, 0.1, 1])
@pytest.mark.parametrize("normalize", [False, True])
@pytest.mark.parametrize("bit_depth", [16, 24, 32])
@pytest.mark.parametrize("sampling_rate", [44100])
def test_magnitude(tmpdir, magnitude, normalize, bit_depth, sampling_rate):
    file = str(tmpdir.join("signal.wav"))
    signal = sine(magnitude=magnitude, sampling_rate=sampling_rate)
    if normalize:
        magnitude = 1.0
    sig, _ = write_and_read(
        file, signal, sampling_rate, bit_depth=bit_depth, normalize=normalize
    )
    assert_allclose(_magnitude(sig), magnitude, rtol=0, atol=tolerance(bit_depth))
    assert type(_magnitude(sig)) is np.float32


@pytest.mark.parametrize("file_type", ["wav", "flac", "mp3", "ogg"])
@pytest.mark.parametrize("sampling_rate", [8000, 48000])
@pytest.mark.parametrize("channels", [1, 2, 8, 255])
@pytest.mark.parametrize("magnitude", [0.01])
def test_file_type(tmpdir, file_type, magnitude, sampling_rate, channels):
    # Skip unallowed combinations
    if file_type == "flac" and channels > 8:
        return None
    if file_type == "mp3" and channels > 2:
        return None

    file = str(tmpdir.join("signal." + file_type))
    signal = sine(
        magnitude=magnitude,
        sampling_rate=sampling_rate,
        channels=channels,
    )
    bit_depth = 16
    sig, fs = write_and_read(file, signal, sampling_rate, bit_depth=bit_depth)
    # Test file type
    assert audeer.file_extension(file) == file_type
    # Test magnitude
    if file_type == "mp3":
        atol = tolerance(8)
    else:
        atol = tolerance(16)
    assert_allclose(
        _magnitude(sig),
        magnitude,
        rtol=0,
        atol=atol,
    )
    # Test metadata
    info = soundfile.info(file)
    assert fs == sampling_rate
    assert info.samplerate == sampling_rate
    assert _channels(sig) == channels
    assert info.channels == channels
    if channels == 1:
        assert sig.ndim == 1
    else:
        assert sig.ndim == 2
    assert _samples(sig) == _samples(signal)
    assert info.frames == _samples(signal)
    if file_type in ["mp3", "ogg"]:
        bit_depth = None
    assert af.bit_depth(file) == bit_depth
    assert af.has_video(file) is False


@pytest.mark.parametrize(
    "file, header_duration, audio, video",  # header duration as given by mediainfo
    [
        ("gs-16b-1c-16000hz.opus", 15.839, True, False),
        ("gs-16b-1c-8000hz.amr", 15.840000, True, False),
        ("gs-16b-1c-44100hz.m4a", 15.833, True, False),
        ("gs-16b-1c-44100hz.aac", None, True, False),
        ("video.mp4", None, False, True),
    ],
)
def test_other_formats(file, header_duration, audio, video):
    path = os.path.join(ASSETS_DIR, file)
    if audio:
        signal, sampling_rate = af.read(path)
        assert af.channels(path) == _channels(signal)
        assert af.sampling_rate(path) == sampling_rate
        assert af.samples(path) == _samples(signal)
        duration = _duration(signal, sampling_rate)
        assert af.duration(path) == duration
        if header_duration is None:
            # Here we expect samplewise precision
            assert af.duration(path, sloppy=True) == duration
        else:
            # Here we expect limited precision
            # as the results differ between soxi and mediainfo
            precision = 1
            sloppy_duration = round(af.duration(path, sloppy=True), precision)
            header_duration = round(header_duration, precision)
            assert sloppy_duration == header_duration
        assert af.bit_depth(path) is None
    assert af.has_video(path) is video


@pytest.mark.parametrize(
    "audio_file",
    [
        (
            np.array([[0.0, 0.0, 0.1, 0.1, 0.2, 0.2]], dtype=np.float32),
            2,  # Hz
        ),
    ],
    indirect=True,
)
# The following test assumes a signal of 3s length,
# containing 0 during the first second,
# 1 during the second second,
# 2 during the third second.
@pytest.mark.parametrize(
    "offset, duration, expected",
    [
        # None | None
        (None, None, [[0.0, 0.0, 0.1, 0.1, 0.2, 0.2]]),
        ("None", "None", [[0.0, 0.0, 0.1, 0.1, 0.2, 0.2]]),
        ("NaN", "NaN", [[0.0, 0.0, 0.1, 0.1, 0.2, 0.2]]),
        ("NaT", "NaT", [[0.0, 0.0, 0.1, 0.1, 0.2, 0.2]]),
        (np.nan, np.nan, [[0.0, 0.0, 0.1, 0.1, 0.2, 0.2]]),
        (pd.NaT, pd.NaT, [[0.0, 0.0, 0.1, 0.1, 0.2, 0.2]]),
        # None | positive
        (None, np.inf, [[0.0, 0.0, 0.1, 0.1, 0.2, 0.2]]),
        # positive | None
        (np.inf, None, [[]]),
        (0.0, None, [[0.0, 0.0, 0.1, 0.1, 0.2, 0.2]]),
        (0.5, None, [[0.0, 0.1, 0.1, 0.2, 0.2]]),
        (1.0, None, [[0.1, 0.1, 0.2, 0.2]]),
        (1.5, None, [[0.1, 0.2, 0.2]]),
        (2.0, None, [[0.2, 0.2]]),
        (2.5, None, [[0.2]]),
        (3.0, None, [[]]),
        (3.5, None, [[]]),
        (4.0, None, [[]]),
        ("Inf", "None", [[]]),
        ("0", "None", [[0.0, 0.0, 0.1, 0.1, 0.2, 0.2]]),
        ("1", "None", [[0.0, 0.1, 0.1, 0.2, 0.2]]),
        ("2", "None", [[0.1, 0.1, 0.2, 0.2]]),
        ("3", "None", [[0.1, 0.2, 0.2]]),
        ("4", "None", [[0.2, 0.2]]),
        ("5", "None", [[0.2]]),
        ("6", "None", [[]]),
        ("7", "None", [[]]),
        ("8", "None", [[]]),
        # positive | positive
        (np.inf, np.inf, [[]]),
        (np.inf, 1.0, [[]]),
        (0.0, np.inf, [[0.0, 0.0, 0.1, 0.1, 0.2, 0.2]]),
        (0.5, np.inf, [[0.0, 0.1, 0.1, 0.2, 0.2]]),
        (1.0, np.inf, [[0.1, 0.1, 0.2, 0.2]]),
        (1.5, np.inf, [[0.1, 0.2, 0.2]]),
        (2.0, np.inf, [[0.2, 0.2]]),
        (2.5, np.inf, [[0.2]]),
        (3.0, np.inf, [[]]),
        (3.5, np.inf, [[]]),
        (0.0, 0.0, [[]]),
        (0.5, 0.0, [[]]),
        (1.0, 0.0, [[]]),
        (1.5, 0.0, [[]]),
        (2.0, 0.0, [[]]),
        (2.5, 0.0, [[]]),
        (0.0, 0.5, [[0.0]]),
        (0.5, 0.5, [[0.0]]),
        (1.0, 0.5, [[0.1]]),
        (1.5, 0.5, [[0.1]]),
        (2.0, 0.5, [[0.2]]),
        (2.5, 0.5, [[0.2]]),
        (3.0, 0.5, [[]]),
        (0.0, 1.0, [[0.0, 0.0]]),
        (0.5, 1.0, [[0.0, 0.1]]),
        (1.0, 1.0, [[0.1, 0.1]]),
        (1.5, 1.0, [[0.1, 0.2]]),
        (2.0, 1.0, [[0.2, 0.2]]),
        (2.5, 1.0, [[0.2]]),
        (3.0, 1.0, [[]]),
        (0.0, 1.5, [[0.0, 0.0, 0.1]]),
        (0.5, 1.5, [[0.0, 0.1, 0.1]]),
        (1.0, 1.5, [[0.1, 0.1, 0.2]]),
        (1.5, 1.5, [[0.1, 0.2, 0.2]]),
        (2.0, 1.5, [[0.2, 0.2]]),
        (2.5, 1.5, [[0.2]]),
        (3.0, 1.5, [[]]),
        (0.0, 2.0, [[0.0, 0.0, 0.1, 0.1]]),
        (0.5, 2.0, [[0.0, 0.1, 0.1, 0.2]]),
        (1.0, 2.0, [[0.1, 0.1, 0.2, 0.2]]),
        (1.5, 2.0, [[0.1, 0.2, 0.2]]),
        (2.0, 2.0, [[0.2, 0.2]]),
        (2.5, 2.0, [[0.2]]),
        (3.0, 2.0, [[]]),
        (0.0, 2.5, [[0.0, 0.0, 0.1, 0.1, 0.2]]),
        (0.5, 2.5, [[0.0, 0.1, 0.1, 0.2, 0.2]]),
        (1.0, 2.5, [[0.1, 0.1, 0.2, 0.2]]),
        (1.5, 2.5, [[0.1, 0.2, 0.2]]),
        (2.0, 2.5, [[0.2, 0.2]]),
        (2.5, 2.5, [[0.2]]),
        (3.0, 2.5, [[]]),
        (0.0, 3.0, [[0.0, 0.0, 0.1, 0.1, 0.2, 0.2]]),
        (0.5, 3.0, [[0.0, 0.1, 0.1, 0.2, 0.2]]),
        (1.0, 3.0, [[0.1, 0.1, 0.2, 0.2]]),
        (1.5, 3.0, [[0.1, 0.2, 0.2]]),
        (2.0, 3.0, [[0.2, 0.2]]),
        (2.5, 3.0, [[0.2]]),
        (3.0, 3.0, [[]]),
        (0.0, 3.5, [[0.0, 0.0, 0.1, 0.1, 0.2, 0.2]]),
        (0.5, 3.5, [[0.0, 0.1, 0.1, 0.2, 0.2]]),
        (1.0, 3.5, [[0.1, 0.1, 0.2, 0.2]]),
        (1.5, 3.5, [[0.1, 0.2, 0.2]]),
        (2.0, 3.5, [[0.2, 0.2]]),
        (2.5, 3.5, [[0.2]]),
        (3.0, 3.5, [[]]),
        (0.0, 4.0, [[0.0, 0.0, 0.1, 0.1, 0.2, 0.2]]),
        ("Inf", "Inf", [[]]),
        ("Inf", "1", [[]]),
        ("0", "Inf", [[0.0, 0.0, 0.1, 0.1, 0.2, 0.2]]),
        ("1", "Inf", [[0.0, 0.1, 0.1, 0.2, 0.2]]),
        ("2", "Inf", [[0.1, 0.1, 0.2, 0.2]]),
        ("3", "Inf", [[0.1, 0.2, 0.2]]),
        ("4", "Inf", [[0.2, 0.2]]),
        ("5", "Inf", [[0.2]]),
        ("6", "Inf", [[]]),
        ("7", "Inf", [[]]),
        ("0", "0", [[]]),
        ("1", "0", [[]]),
        ("2", "0", [[]]),
        ("3", "0", [[]]),
        ("4", "0", [[]]),
        ("5", "0", [[]]),
        ("0", "1", [[0.0]]),
        ("1", "1", [[0.0]]),
        ("2", "1", [[0.1]]),
        ("3", "1", [[0.1]]),
        ("4", "1", [[0.2]]),
        ("5", "1", [[0.2]]),
        ("6", "1", [[]]),
        ("0", "2", [[0.0, 0.0]]),
        ("1", "2", [[0.0, 0.1]]),
        ("2", "2", [[0.1, 0.1]]),
        ("3", "2", [[0.1, 0.2]]),
        ("4", "2", [[0.2, 0.2]]),
        ("5", "2", [[0.2]]),
        ("6", "2", [[]]),
        ("0", "3", [[0.0, 0.0, 0.1]]),
        ("1", "3", [[0.0, 0.1, 0.1]]),
        ("2", "3", [[0.1, 0.1, 0.2]]),
        ("3", "3", [[0.1, 0.2, 0.2]]),
        ("4", "3", [[0.2, 0.2]]),
        ("5", "3", [[0.2]]),
        ("6", "3", [[]]),
        ("0", "4", [[0.0, 0.0, 0.1, 0.1]]),
        ("1", "4", [[0.0, 0.1, 0.1, 0.2]]),
        ("2", "4", [[0.1, 0.1, 0.2, 0.2]]),
        ("3", "4", [[0.1, 0.2, 0.2]]),
        ("4", "4", [[0.2, 0.2]]),
        ("5", "4", [[0.2]]),
        ("6", "4", [[]]),
        ("0", "5", [[0.0, 0.0, 0.1, 0.1, 0.2]]),
        ("1", "5", [[0.0, 0.1, 0.1, 0.2, 0.2]]),
        ("2", "5", [[0.1, 0.1, 0.2, 0.2]]),
        ("3", "5", [[0.1, 0.2, 0.2]]),
        ("4", "5", [[0.2, 0.2]]),
        ("5", "5", [[0.2]]),
        ("6", "5", [[]]),
        ("0", "6", [[0.0, 0.0, 0.1, 0.1, 0.2, 0.2]]),
        ("1", "6", [[0.0, 0.1, 0.1, 0.2, 0.2]]),
        ("2", "6", [[0.1, 0.1, 0.2, 0.2]]),
        ("3", "6", [[0.1, 0.2, 0.2]]),
        ("4", "6", [[0.2, 0.2]]),
        ("5", "6", [[0.2]]),
        ("6", "6", [[]]),
        ("0", "7", [[0.0, 0.0, 0.1, 0.1, 0.2, 0.2]]),
        ("1", "7", [[0.0, 0.1, 0.1, 0.2, 0.2]]),
        ("2", "7", [[0.1, 0.1, 0.2, 0.2]]),
        ("3", "7", [[0.1, 0.2, 0.2]]),
        ("4", "7", [[0.2, 0.2]]),
        ("5", "7", [[0.2]]),
        ("6", "7", [[]]),
        ("0", "8", [[0.0, 0.0, 0.1, 0.1, 0.2, 0.2]]),
        # None | negative
        (None, -np.inf, [[0.0, 0.0, 0.1, 0.1, 0.2, 0.2]]),
        (None, -0.5, [[0.2]]),
        (None, -1.0, [[0.2, 0.2]]),
        (None, -1.5, [[0.1, 0.2, 0.2]]),
        (None, -2.0, [[0.1, 0.1, 0.2, 0.2]]),
        (None, -2.5, [[0.0, 0.1, 0.1, 0.2, 0.2]]),
        (None, -3.0, [[0.0, 0.0, 0.1, 0.1, 0.2, 0.2]]),
        (None, -3.5, [[0.0, 0.0, 0.1, 0.1, 0.2, 0.2]]),
        (None, -4.0, [[0.0, 0.0, 0.1, 0.1, 0.2, 0.2]]),
        ("None", "-Inf", [[0.0, 0.0, 0.1, 0.1, 0.2, 0.2]]),
        ("None", "-1", [[0.2]]),
        ("None", "-2", [[0.2, 0.2]]),
        ("None", "-3", [[0.1, 0.2, 0.2]]),
        ("None", "-4", [[0.1, 0.1, 0.2, 0.2]]),
        ("None", "-5", [[0.0, 0.1, 0.1, 0.2, 0.2]]),
        ("None", "-6", [[0.0, 0.0, 0.1, 0.1, 0.2, 0.2]]),
        ("None", "-7", [[0.0, 0.0, 0.1, 0.1, 0.2, 0.2]]),
        ("None", "-8", [[0.0, 0.0, 0.1, 0.1, 0.2, 0.2]]),
        # negative | None
        (-np.inf, None, [[0.0, 0.0, 0.1, 0.1, 0.2, 0.2]]),
        (-0.5, None, [[0.2]]),
        (-1.0, None, [[0.2, 0.2]]),
        (-1.5, None, [[0.1, 0.2, 0.2]]),
        (-2.0, None, [[0.1, 0.1, 0.2, 0.2]]),
        (-2.5, None, [[0.0, 0.1, 0.1, 0.2, 0.2]]),
        (-3.0, None, [[0.0, 0.0, 0.1, 0.1, 0.2, 0.2]]),
        (-3.5, None, [[0.0, 0.0, 0.1, 0.1, 0.2, 0.2]]),
        (-4.0, None, [[0.0, 0.0, 0.1, 0.1, 0.2, 0.2]]),
        ("-Inf", "None", [[0.0, 0.0, 0.1, 0.1, 0.2, 0.2]]),
        ("-1", "None", [[0.2]]),
        ("-2", "None", [[0.2, 0.2]]),
        ("-3", "None", [[0.1, 0.2, 0.2]]),
        ("-4", "None", [[0.1, 0.1, 0.2, 0.2]]),
        ("-5", "None", [[0.0, 0.1, 0.1, 0.2, 0.2]]),
        ("-6", "None", [[0.0, 0.0, 0.1, 0.1, 0.2, 0.2]]),
        ("-7", "None", [[0.0, 0.0, 0.1, 0.1, 0.2, 0.2]]),
        ("-7", "None", [[0.0, 0.0, 0.1, 0.1, 0.2, 0.2]]),
        # negative | positive
        (-np.inf, np.inf, [[0.0, 0.0, 0.1, 0.1, 0.2, 0.2]]),
        (-np.inf, 4.0, [[]]),
        (-4.0, np.inf, [[0.0, 0.0, 0.1, 0.1, 0.2, 0.2]]),
        (-0.5, 0.0, [[]]),
        (-1.0, 0.0, [[]]),
        (-1.5, 0.0, [[]]),
        (-2.0, 0.0, [[]]),
        (-2.5, 0.0, [[]]),
        (-3.0, 0.0, [[]]),
        (-3.5, 0.0, [[]]),
        (-4.0, 0.0, [[]]),
        (-0.5, 0.5, [[0.2]]),
        (-1.0, 0.5, [[0.2]]),
        (-1.5, 0.5, [[0.1]]),
        (-2.0, 0.5, [[0.1]]),
        (-2.5, 0.5, [[0.0]]),
        (-3.0, 0.5, [[0.0]]),
        (-3.5, 0.5, [[]]),
        (-4.0, 0.5, [[]]),
        (-0.5, 1.0, [[0.2]]),
        (-1.0, 1.0, [[0.2, 0.2]]),
        (-1.5, 1.0, [[0.1, 0.2]]),
        (-2.0, 1.0, [[0.1, 0.1]]),
        (-2.5, 1.0, [[0.0, 0.1]]),
        (-3.0, 1.0, [[0.0, 0.0]]),
        (-3.5, 1.0, [[0.0]]),
        (-4.0, 1.0, [[]]),
        (-0.5, 1.5, [[0.2]]),
        (-1.0, 1.5, [[0.2, 0.2]]),
        (-1.5, 1.5, [[0.1, 0.2, 0.2]]),
        (-2.0, 1.5, [[0.1, 0.1, 0.2]]),
        (-2.5, 1.5, [[0.0, 0.1, 0.1]]),
        (-3.0, 1.5, [[0.0, 0.0, 0.1]]),
        (-3.5, 1.5, [[0.0, 0.0]]),
        (-4.0, 1.5, [[0.0]]),
        (-4.5, 1.5, [[]]),
        (-0.5, 2.0, [[0.2]]),
        (-1.0, 2.0, [[0.2, 0.2]]),
        (-1.5, 2.0, [[0.1, 0.2, 0.2]]),
        (-2.0, 2.0, [[0.1, 0.1, 0.2, 0.2]]),
        (-2.5, 2.0, [[0.0, 0.1, 0.1, 0.2]]),
        (-3.0, 2.0, [[0.0, 0.0, 0.1, 0.1]]),
        (-3.5, 2.0, [[0.0, 0.0, 0.1]]),
        (-4.0, 2.0, [[0.0, 0.0]]),
        (-4.5, 2.0, [[0.0]]),
        (-5.0, 2.0, [[]]),
        ("-Inf", "Inf", [[0.0, 0.0, 0.1, 0.1, 0.2, 0.2]]),
        ("-Inf", "8", [[]]),
        ("-8", "Inf", [[0.0, 0.0, 0.1, 0.1, 0.2, 0.2]]),
        ("-1", "0", [[]]),
        ("-2", "0", [[]]),
        ("-3", "0", [[]]),
        ("-4", "0", [[]]),
        ("-5", "0", [[]]),
        ("-6", "0", [[]]),
        ("-7", "0", [[]]),
        ("-8", "0", [[]]),
        ("-1", "1", [[0.2]]),
        ("-2", "1", [[0.2]]),
        ("-3", "1", [[0.1]]),
        ("-4", "1", [[0.1]]),
        ("-5", "1", [[0.0]]),
        ("-6", "1", [[0.0]]),
        ("-7", "1", [[]]),
        ("-8", "1", [[]]),
        ("-1", "2", [[0.2]]),
        ("-2", "2", [[0.2, 0.2]]),
        ("-3", "2", [[0.1, 0.2]]),
        ("-4", "2", [[0.1, 0.1]]),
        ("-5", "2", [[0.0, 0.1]]),
        ("-6", "2", [[0.0, 0.0]]),
        ("-7", "2", [[0.0]]),
        ("-8", "2", [[]]),
        ("-1", "3", [[0.2]]),
        ("-2", "3", [[0.2, 0.2]]),
        ("-3", "3", [[0.1, 0.2, 0.2]]),
        ("-4", "3", [[0.1, 0.1, 0.2]]),
        ("-5", "3", [[0.0, 0.1, 0.1]]),
        ("-6", "3", [[0.0, 0.0, 0.1]]),
        ("-7", "3", [[0.0, 0.0]]),
        ("-8", "3", [[0.0]]),
        ("-9", "3", [[]]),
        ("-1", "4", [[0.2]]),
        ("-2", "4", [[0.2, 0.2]]),
        ("-3", "4", [[0.1, 0.2, 0.2]]),
        ("-4", "4", [[0.1, 0.1, 0.2, 0.2]]),
        ("-5", "4", [[0.0, 0.1, 0.1, 0.2]]),
        ("-6", "4", [[0.0, 0.0, 0.1, 0.1]]),
        ("-7", "4", [[0.0, 0.0, 0.1]]),
        ("-8", "4", [[0.0, 0.0]]),
        ("-9", "4", [[0.0]]),
        ("-10", "4", [[]]),
        # positive | negative
        (np.inf, -np.inf, [[0.0, 0.0, 0.1, 0.1, 0.2, 0.2]]),
        (np.inf, -4.0, [[]]),
        (4.0, -np.inf, [[0.0, 0.0, 0.1, 0.1, 0.2, 0.2]]),
        (2.0, -np.inf, [[0.0, 0.0, 0.1, 0.1]]),
        (0.0, -0.5, [[]]),
        (0.5, -0.5, [[0.0]]),
        (1.0, -0.5, [[0.0]]),
        (1.5, -0.5, [[0.1]]),
        (2.0, -0.5, [[0.1]]),
        (2.5, -0.5, [[0.2]]),
        (3.0, -0.5, [[0.2]]),
        (3.5, -0.5, [[]]),
        (4.0, -0.5, [[]]),
        (0.0, -1.0, [[]]),
        (0.5, -1.0, [[0.0]]),
        (1.0, -1.0, [[0.0, 0.0]]),
        (1.5, -1.0, [[0.0, 0.1]]),
        (2.0, -1.0, [[0.1, 0.1]]),
        (2.5, -1.0, [[0.1, 0.2]]),
        (3.0, -1.0, [[0.2, 0.2]]),
        (3.5, -1.0, [[0.2]]),
        (4.0, -1.0, [[]]),
        (0.0, -1.5, [[]]),
        (0.5, -1.5, [[0.0]]),
        (1.0, -1.5, [[0.0, 0.0]]),
        (1.5, -1.5, [[0.0, 0.0, 0.1]]),
        (2.0, -1.5, [[0.0, 0.1, 0.1]]),
        (2.5, -1.5, [[0.1, 0.1, 0.2]]),
        (3.0, -1.5, [[0.1, 0.2, 0.2]]),
        (3.5, -1.5, [[0.2, 0.2]]),
        (4.0, -1.5, [[0.2]]),
        (4.5, -1.5, [[]]),
        (0.0, -2.0, [[]]),
        (0.5, -2.0, [[0.0]]),
        (1.0, -2.0, [[0.0, 0.0]]),
        (1.5, -2.0, [[0.0, 0.0, 0.1]]),
        (2.0, -2.0, [[0.0, 0.0, 0.1, 0.1]]),
        (2.5, -2.0, [[0.0, 0.1, 0.1, 0.2]]),
        (3.0, -2.0, [[0.1, 0.1, 0.2, 0.2]]),
        (3.5, -2.0, [[0.1, 0.2, 0.2]]),
        (4.0, -2.0, [[0.2, 0.2]]),
        (4.5, -2.0, [[0.2]]),
        (5.0, -2.0, [[]]),
        (2.0, -2.5, [[0.0, 0.0, 0.1, 0.1]]),
        (2.5, -2.5, [[0.0, 0.0, 0.1, 0.1, 0.2]]),
        (3.0, -2.5, [[0.0, 0.1, 0.1, 0.2, 0.2]]),
        (3.5, -2.5, [[0.1, 0.1, 0.2, 0.2]]),
        (4.0, -2.5, [[0.1, 0.2, 0.2]]),
        (4.5, -2.5, [[0.2, 0.2]]),
        (5.0, -2.5, [[0.2]]),
        (5.5, -2.5, [[]]),
        (2.0, -3.0, [[0.0, 0.0, 0.1, 0.1]]),
        (2.5, -3.0, [[0.0, 0.0, 0.1, 0.1, 0.2]]),
        (3.0, -3.0, [[0.0, 0.0, 0.1, 0.1, 0.2, 0.2]]),
        (3.5, -3.0, [[0.0, 0.1, 0.1, 0.2, 0.2]]),
        (4.0, -3.0, [[0.1, 0.1, 0.2, 0.2]]),
        (4.5, -3.0, [[0.1, 0.2, 0.2]]),
        (5.0, -3.0, [[0.2, 0.2]]),
        (5.5, -3.0, [[0.2]]),
        (6.0, -3.0, [[]]),
        (3.0, -3.5, [[0.0, 0.0, 0.1, 0.1, 0.2, 0.2]]),
        (3.0, -4.0, [[0.0, 0.0, 0.1, 0.1, 0.2, 0.2]]),
        ("Inf", "-Inf", [[0.0, 0.0, 0.1, 0.1, 0.2, 0.2]]),
        ("Inf", "-8", [[]]),
        ("8", "-Inf", [[0.0, 0.0, 0.1, 0.1, 0.2, 0.2]]),
        ("4", "-Inf", [[0.0, 0.0, 0.1, 0.1]]),
        ("0", "-1", [[]]),
        ("1", "-1", [[0.0]]),
        ("2", "-1", [[0.0]]),
        ("3", "-1", [[0.1]]),
        ("4", "-1", [[0.1]]),
        ("5", "-1", [[0.2]]),
        ("6", "-1", [[0.2]]),
        ("7", "-1", [[]]),
        ("8", "-1", [[]]),
        ("0", "-2", [[]]),
        ("1", "-2", [[0.0]]),
        ("2", "-2", [[0.0, 0.0]]),
        ("3", "-2", [[0.0, 0.1]]),
        ("4", "-2", [[0.1, 0.1]]),
        ("5", "-2", [[0.1, 0.2]]),
        ("6", "-2", [[0.2, 0.2]]),
        ("7", "-2", [[0.2]]),
        ("8", "-2", [[]]),
        ("0", "-3", [[]]),
        ("1", "-3", [[0.0]]),
        ("2", "-3", [[0.0, 0.0]]),
        ("3", "-3", [[0.0, 0.0, 0.1]]),
        ("4", "-3", [[0.0, 0.1, 0.1]]),
        ("5", "-3", [[0.1, 0.1, 0.2]]),
        ("6", "-3", [[0.1, 0.2, 0.2]]),
        ("7", "-3", [[0.2, 0.2]]),
        ("8", "-3", [[0.2]]),
        ("9", "-3", [[]]),
        ("0", "-4", [[]]),
        ("1", "-4", [[0.0]]),
        ("2", "-4", [[0.0, 0.0]]),
        ("3", "-4", [[0.0, 0.0, 0.1]]),
        ("4", "-4", [[0.0, 0.0, 0.1, 0.1]]),
        ("5", "-4", [[0.0, 0.1, 0.1, 0.2]]),
        ("6", "-4", [[0.1, 0.1, 0.2, 0.2]]),
        ("7", "-4", [[0.1, 0.2, 0.2]]),
        ("8", "-4", [[0.2, 0.2]]),
        ("9", "-4", [[0.2]]),
        ("10", "-4", [[]]),
        ("4", "-5", [[0.0, 0.0, 0.1, 0.1]]),
        ("5", "-5", [[0.0, 0.0, 0.1, 0.1, 0.2]]),
        ("6", "-5", [[0.0, 0.1, 0.1, 0.2, 0.2]]),
        ("7", "-5", [[0.1, 0.1, 0.2, 0.2]]),
        ("8", "-5", [[0.1, 0.2, 0.2]]),
        ("9", "-5", [[0.2, 0.2]]),
        ("10", "-5", [[0.2]]),
        ("11", "-5", [[]]),
        ("4", "-6", [[0.0, 0.0, 0.1, 0.1]]),
        ("5", "-6", [[0.0, 0.0, 0.1, 0.1, 0.2]]),
        ("6", "-6", [[0.0, 0.0, 0.1, 0.1, 0.2, 0.2]]),
        ("7", "-6", [[0.0, 0.1, 0.1, 0.2, 0.2]]),
        ("8", "-6", [[0.1, 0.1, 0.2, 0.2]]),
        ("9", "-6", [[0.1, 0.2, 0.2]]),
        ("10", "-6", [[0.2, 0.2]]),
        ("11", "-6", [[0.2]]),
        ("12", "-6", [[]]),
        ("6", "-6", [[0.0, 0.0, 0.1, 0.1, 0.2, 0.2]]),
        ("6", "-7", [[0.0, 0.0, 0.1, 0.1, 0.2, 0.2]]),
        ("6", "-8", [[0.0, 0.0, 0.1, 0.1, 0.2, 0.2]]),
        # negative | negative
        (-np.inf, -np.inf, [[]]),
        (-np.inf, -4.0, [[]]),
        (-4.0, -np.inf, [[]]),
        (-0.5, -0.5, [[0.2]]),
        (-1.0, -0.5, [[0.1]]),
        (-1.5, -0.5, [[0.1]]),
        (-2.0, -0.5, [[0.0]]),
        (-2.5, -0.5, [[0.0]]),
        (-3.0, -0.5, [[]]),
        (-3.5, -0.5, [[]]),
        (-4.0, -0.5, [[]]),
        (-0.5, -1.0, [[0.1, 0.2]]),
        (-1.0, -1.0, [[0.1, 0.1]]),
        (-1.5, -1.0, [[0.0, 0.1]]),
        (-2.0, -1.0, [[0.0, 0.0]]),
        (-2.5, -1.0, [[0.0]]),
        (-3.0, -1.0, [[]]),
        (-3.5, -1.0, [[]]),
        (-4.0, -1.0, [[]]),
        (-0.5, -1.5, [[0.1, 0.1, 0.2]]),
        (-1.0, -1.5, [[0.0, 0.1, 0.1]]),
        (-1.5, -1.5, [[0.0, 0.0, 0.1]]),
        (-2.0, -1.5, [[0.0, 0.0]]),
        (-2.5, -1.5, [[0.0]]),
        (-3.0, -1.5, [[]]),
        (-3.5, -1.5, [[]]),
        (-4.0, -1.5, [[]]),
        (-0.5, -2.0, [[0.0, 0.1, 0.1, 0.2]]),
        (-1.0, -2.0, [[0.0, 0.0, 0.1, 0.1]]),
        (-1.5, -2.0, [[0.0, 0.0, 0.1]]),
        (-2.0, -2.0, [[0.0, 0.0]]),
        (-2.5, -2.0, [[0.0]]),
        (-3.0, -2.0, [[]]),
        (-3.5, -2.0, [[]]),
        (-4.0, -2.0, [[]]),
        (-0.5, -2.5, [[0.0, 0.0, 0.1, 0.1, 0.2]]),
        (-1.0, -2.5, [[0.0, 0.0, 0.1, 0.1]]),
        (-1.5, -2.5, [[0.0, 0.0, 0.1]]),
        (-2.0, -2.5, [[0.0, 0.0]]),
        (-2.5, -2.5, [[0.0]]),
        (-3.0, -2.5, [[]]),
        (-3.5, -2.5, [[]]),
        (-4.0, -2.5, [[]]),
        (-0.5, -3.0, [[0.0, 0.0, 0.1, 0.1, 0.2]]),
        (-1.0, -3.0, [[0.0, 0.0, 0.1, 0.1]]),
        (-1.5, -3.0, [[0.0, 0.0, 0.1]]),
        (-2.0, -3.0, [[0.0, 0.0]]),
        (-2.5, -3.0, [[0.0]]),
        (-3.0, -3.0, [[]]),
        (-3.5, -3.0, [[]]),
        (-4.0, -3.0, [[]]),
        (-0.5, -3.5, [[0.0, 0.0, 0.1, 0.1, 0.2]]),
        (-1.0, -3.5, [[0.0, 0.0, 0.1, 0.1]]),
        (-1.5, -3.5, [[0.0, 0.0, 0.1]]),
        (-2.0, -3.5, [[0.0, 0.0]]),
        (-2.5, -3.5, [[0.0]]),
        (-3.0, -3.5, [[]]),
        (-3.5, -3.5, [[]]),
        (-4.0, -3.5, [[]]),
        (-0.5, -4.0, [[0.0, 0.0, 0.1, 0.1, 0.2]]),
        (-1.0, -4.0, [[0.0, 0.0, 0.1, 0.1]]),
        (-1.5, -4.0, [[0.0, 0.0, 0.1]]),
        (-2.0, -4.0, [[0.0, 0.0]]),
        (-2.5, -4.0, [[0.0]]),
        (-3.0, -4.0, [[]]),
        (-3.5, -4.0, [[]]),
        (-4.0, -4.0, [[]]),
        ("-Inf", "-Inf", [[]]),
        ("-Inf", "-8", [[]]),
        ("-8", "-Inf", [[]]),
        ("-1", "-1", [[0.2]]),
        ("-2", "-1", [[0.1]]),
        ("-3", "-1", [[0.1]]),
        ("-4", "-1", [[0.0]]),
        ("-5", "-1", [[0.0]]),
        ("-6", "-1", [[]]),
        ("-7", "-1", [[]]),
        ("-8", "-1", [[]]),
        ("-1", "-2", [[0.1, 0.2]]),
        ("-2", "-2", [[0.1, 0.1]]),
        ("-3", "-2", [[0.0, 0.1]]),
        ("-4", "-2", [[0.0, 0.0]]),
        ("-5", "-2", [[0.0]]),
        ("-6", "-2", [[]]),
        ("-7", "-2", [[]]),
        ("-8", "-2", [[]]),
        ("-1", "-3", [[0.1, 0.1, 0.2]]),
        ("-2", "-3", [[0.0, 0.1, 0.1]]),
        ("-3", "-3", [[0.0, 0.0, 0.1]]),
        ("-4", "-3", [[0.0, 0.0]]),
        ("-5", "-3", [[0.0]]),
        ("-6", "-3", [[]]),
        ("-7", "-3", [[]]),
        ("-8", "-3", [[]]),
        ("-1", "-4", [[0.0, 0.1, 0.1, 0.2]]),
        ("-2", "-4", [[0.0, 0.0, 0.1, 0.1]]),
        ("-3", "-4", [[0.0, 0.0, 0.1]]),
        ("-4", "-4", [[0.0, 0.0]]),
        ("-5", "-4", [[0.0]]),
        ("-6", "-4", [[]]),
        ("-7", "-4", [[]]),
        ("-8", "-4", [[]]),
        ("-1", "-5", [[0.0, 0.0, 0.1, 0.1, 0.2]]),
        ("-2", "-5", [[0.0, 0.0, 0.1, 0.1]]),
        ("-3", "-5", [[0.0, 0.0, 0.1]]),
        ("-4", "-5", [[0.0, 0.0]]),
        ("-5", "-5", [[0.0]]),
        ("-6", "-5", [[]]),
        ("-7", "-5", [[]]),
        ("-8", "-5", [[]]),
        ("-1", "-6", [[0.0, 0.0, 0.1, 0.1, 0.2]]),
        ("-2", "-6", [[0.0, 0.0, 0.1, 0.1]]),
        ("-3", "-6", [[0.0, 0.0, 0.1]]),
        ("-4", "-6", [[0.0, 0.0]]),
        ("-5", "-6", [[0.0]]),
        ("-6", "-6", [[]]),
        ("-7", "-6", [[]]),
        ("-8", "-6", [[]]),
        ("-1", "-7", [[0.0, 0.0, 0.1, 0.1, 0.2]]),
        ("-2", "-7", [[0.0, 0.0, 0.1, 0.1]]),
        ("-3", "-7", [[0.0, 0.0, 0.1]]),
        ("-4", "-7", [[0.0, 0.0]]),
        ("-5", "-7", [[0.0]]),
        ("-6", "-7", [[]]),
        ("-7", "-7", [[]]),
        ("-8", "-7", [[]]),
        ("-1", "-8", [[0.0, 0.0, 0.1, 0.1, 0.2]]),
        ("-2", "-8", [[0.0, 0.0, 0.1, 0.1]]),
        ("-3", "-8", [[0.0, 0.0, 0.1]]),
        ("-4", "-8", [[0.0, 0.0]]),
        ("-5", "-8", [[0.0]]),
        ("-6", "-8", [[]]),
        ("-7", "-8", [[]]),
        ("-8", "-8", [[]]),
    ],
)
def test_read_duration_and_offset(audio_file, offset, duration, expected):
    # Read with provided duration/offset
    signal, _ = af.read(
        audio_file,
        offset=offset,
        duration=duration,
        always_2d=True,
    )
    np.testing.assert_allclose(
        signal,
        np.array(expected, dtype=np.float32),
        rtol=1e-03,
    )


def test_read_duration_and_offset_file_formats(tmpdir):
    # Prepare signals
    sampling_rate = 44100
    channels = 1
    signal = sine(
        magnitude=1,
        sampling_rate=sampling_rate,
        channels=channels,
    )
    wav_file = str(tmpdir.join("signal.wav"))
    mp3_file = str(tmpdir.join("signal.mp3"))
    m4a_file = audeer.path(ASSETS_DIR, "gs-16b-1c-44100hz.m4a")
    af.write(wav_file, signal, sampling_rate)
    af.write(mp3_file, signal, sampling_rate)

    for file in [wav_file, mp3_file, m4a_file]:
        # Duration and offset in seconds
        offset = 0.1
        duration = 0.5
        sig, fs = af.read(file, offset=offset, duration=duration)
        assert _duration(sig, sampling_rate) == duration
        sig, fs = af.read(file, offset=offset)
        assert_allclose(
            _duration(sig, sampling_rate),
            af.duration(file) - offset,
            rtol=0,
            atol=tolerance("duration", sampling_rate),
        )

        # Duration and offset in negative seconds
        offset = -0.1
        duration = -0.5
        sig, fs = af.read(file, offset=offset, duration=duration)
        assert _duration(sig, sampling_rate) == -duration
        sig, fs = af.read(file, offset=af.duration(file) + offset)
        assert_allclose(
            _duration(sig, sampling_rate),
            -offset,
            rtol=0,
            atol=tolerance("duration", sampling_rate),
        )

        # Duration and offset in samples
        offset = "100"
        duration = "200"
        duration_s = float(duration) / sampling_rate
        offset_s = float(offset) / sampling_rate
        sig, fs = af.read(
            file,
            offset=offset,
            duration=duration,
            always_2d=True,
        )
        assert _duration(sig, sampling_rate) == duration_s
        assert sig.shape[1] == float(duration)
        sig, fs = af.read(file, offset=offset)
        assert_allclose(
            _duration(sig, sampling_rate),
            af.duration(file) - offset_s,
            rtol=0,
            atol=tolerance("duration", sampling_rate),
        )

        # Duration that results in empty signal
        duration = 0.000001
        sig, fs = af.read(file, duration=duration)
        np.testing.assert_array_equal(
            sig,
            np.array([], np.float32),
        )


@pytest.mark.parametrize(
    "audio_file",
    [
        (
            np.array(
                [[0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]],
                dtype=np.float32,
            ),
            10,  # Hz
        ),
    ],
    indirect=True,
)
@pytest.mark.parametrize(
    # offset and duration need to be given in seconds
    "offset, duration, expected",
    [
        (0.1, 0.1, [0.1]),
        (0.1, 0.03, []),
        (0.1, 0.15, [0.1, 0.2]),
        (0.1, 0.19, [0.1, 0.2]),
        (0.049, 0.19, [0.0, 0.1]),
        (0.15, 0.15, [0.2, 0.3]),
    ],
)
def test_read_duration_and_offset_rounding(
    tmpdir,
    audio_file,
    offset,
    duration,
    expected,
):
    # Prepare signals

    # Ensure that the rounding from duration to samples
    # is done as expected
    # and in the same way
    # when reading with sox or ffmpeg

    # soundfile
    signal, sampling_rate = af.read(audio_file, offset=offset, duration=duration)
    np.testing.assert_allclose(
        signal,
        np.array(expected, dtype=np.float32),
        rtol=1e-03,
    )

    if len(expected) == 0:
        # duration of 0 is handled inside af.read()
        # even when duration is only 0 after rounding
        # as ffmpeg cannot handle those cases
        return None

    # sox
    convert_file = str(tmpdir.join("signal-sox.wav"))
    try:
        af.core.utils.run_sox(audio_file, convert_file, offset, duration, sampling_rate)
        signal, _ = af.read(convert_file)
        np.testing.assert_allclose(
            signal,
            np.array(expected, dtype=np.float32),
            rtol=1e-03,
        )
    except FileNotFoundError:
        # When testing without an installation of sox
        pass

    # ffmpeg
    convert_file = str(tmpdir.join("signal-ffmpeg.wav"))
    af.core.utils.run_ffmpeg(audio_file, convert_file, offset, duration, sampling_rate)
    signal, _ = af.read(convert_file)
    np.testing.assert_allclose(
        signal,
        np.array(expected, dtype=np.float32),
        rtol=1e-03,
    )


def test_write_errors():
    sampling_rate = 44100

    # Call with unallowed bit depths
    expected_error = '"bit_depth" has to be one of'
    with pytest.raises(RuntimeError, match=expected_error):
        af.write("test.wav", np.zeros((1, 100)), sampling_rate, bit_depth=1)

    # Checking for not allowed combinations of channel and file type
    expected_error = (
        "The maximum number of allowed channels "
        "for 'flac' is 8. Consider using 'wav' instead."
    )
    with pytest.raises(RuntimeError, match=expected_error):
        write_and_read("test.flac", np.zeros((9, 100)), sampling_rate)
    expected_error = (
        "The maximum number of allowed channels "
        "for 'mp3' is 2. Consider using 'wav' instead."
    )
    with pytest.raises(RuntimeError, match=expected_error):
        write_and_read("test.mp3", np.zeros((3, 100)), sampling_rate)
    expected_error = (
        "The maximum number of allowed channels "
        "for 'ogg' is 255. Consider using 'wav' instead."
    )
    with pytest.raises(RuntimeError, match=expected_error):
        write_and_read("test.ogg", np.zeros((256, 100)), sampling_rate)
    expected_error = "The maximum number of allowed channels " "for 'wav' is 65535."
    with pytest.raises(RuntimeError, match=expected_error):
        write_and_read("test.wav", np.zeros((65536, 100)), sampling_rate)
