from __future__ import division
import os
import subprocess
import tempfile

import pytest
import numpy as np
from numpy.testing import assert_allclose
import soundfile

import audeer
import audiofile as af


SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
ASSETS_DIR = os.path.join(SCRIPT_DIR, 'assets')


@pytest.fixture(scope='function')
def empty_file(tmpdir, request):
    """Fixture to generate empty audio files.

    The request parameter allows to select the file extension.

    """
    # Create empty audio file
    empty_file = os.path.join(tmpdir, 'empty-file.wav')
    af.write(empty_file, np.array([[]]), 16000)

    # Rename to match extension
    file_ext = request.param
    ofpath = audeer.replace_file_extension(empty_file, file_ext)
    if os.path.exists(empty_file):
        os.rename(empty_file, ofpath)

    yield ofpath

    if os.path.exists(ofpath):
        os.remove(ofpath)


@pytest.fixture(scope='function')
def hide_system_path():
    """Fixture to hide system path in test."""
    current_path = os.environ['PATH']
    os.environ['PATH'] = ''

    yield

    os.environ['PATH'] = current_path


@pytest.fixture(scope='function')
def non_audio_file(tmpdir, request):
    """Fixture to generate broken audio files.

    The request parameter allows to select the file extension.

    """
    # Create empty file to simulate broken/non-audio file
    file_ext = request.param
    broken_file = os.path.join(tmpdir, f'broken-file.{file_ext}')
    open(broken_file, 'w').close()

    yield broken_file

    if os.path.exists(broken_file):
        os.remove(broken_file)


def convert_to_mp3(infile, outfile, sampling_rate, channels):
    """Convert file to MP3 using ffmpeg."""
    subprocess.call(
        [
            'ffmpeg',
            '-i', infile,
            '-vn',
            '-ar', str(sampling_rate),
            '-ac', str(channels),
            '-b:a', '192k',
            outfile,
        ]
    )


def tolerance(condition, sampling_rate=0):
    """Absolute tolerance for different condition."""
    tol = 0
    if condition == 8:
        tol = 2 ** -7
    elif condition == 16:
        tol = 2 ** -11  # half precision
    elif condition == 24:
        tol = 2 ** -17  # to be checked
    elif condition == 32:
        tol = 2 ** -24  # single precision
    elif condition == 'duration':
        tol = 1 / sampling_rate
    return tol


def ensure_two_dimensions(x):
    """Converts (n,) to (1, n)."""
    return np.atleast_2d(x)


def sine(duration=1,
         sampling_rate=44100,
         channels=1,
         magnitude=1,
         frequency=100):
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


@pytest.mark.parametrize('duration', [-1.0, -1, 0, 0.0])
@pytest.mark.parametrize('offset', [0, 1])
def test_read(tmpdir, duration, offset):
    file = str(tmpdir.join('signal.wav'))
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
    'convert',
    (True, False),
)
@pytest.mark.parametrize(
    'empty_file',
    ('bin', 'mp3', 'wav'),
    indirect=True,
)
def test_empty_file(tmpdir, convert, empty_file):
    if convert:
        converted_file = str(tmpdir.join('signal-converted.wav'))
        af.convert_to_wav(empty_file, converted_file)
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
    if audeer.file_extension(empty_file) == 'wav':
        assert af.bit_depth(empty_file) == 16
    else:
        assert af.bit_depth(empty_file) is None


@pytest.mark.parametrize(
    'empty_file',
    ('bin', 'mp3'),
    indirect=True,
)
def test_missing_binaries(tmpdir, hide_system_path, empty_file):
    expected_error = FileNotFoundError
    # Reading file
    with pytest.raises(expected_error, match='ffmpeg'):
        signal, sampling_rate = af.read(empty_file)
    # Metadata
    with pytest.raises(expected_error, match='mediainfo'):
        af.channels(empty_file)
    with pytest.raises(expected_error, match='ffmpeg'):
        af.duration(empty_file)
    with pytest.raises(expected_error, match='mediainfo'):
        af.duration(empty_file, sloppy=True)
    with pytest.raises(expected_error, match='ffmpeg'):
        af.samples(empty_file)
    with pytest.raises(expected_error, match='mediainfo'):
        af.sampling_rate(empty_file)

    # Convert
    with pytest.raises(expected_error, match='ffmpeg'):
        converted_file = str(tmpdir.join('signal-converted.wav'))
        af.convert_to_wav(empty_file, converted_file)


@pytest.mark.parametrize(
    'ext',
    ('bin', 'mp3', 'wav'),
)
def test_missing_file(tmpdir, ext):
    missing_file = f'missing_file.{ext}'
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
        converted_file = str(tmpdir.join('signal-converted.wav'))
        af.convert_to_wav(missing_file, converted_file)


@pytest.mark.parametrize(
    'non_audio_file',
    ('bin', 'mp3', 'wav'),
    indirect=True,
)
def test_broken_file(tmpdir, non_audio_file):
    # Only match the beginning of error message
    # as the default soundfile message differs at the end on macOS
    error_msg = 'Error opening'
    expected_error = RuntimeError
    # Reading file
    with pytest.raises(expected_error, match=error_msg):
        af.read(non_audio_file)
    # Metadata
    if audeer.file_extension(non_audio_file) == 'wav':
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
        converted_file = str(tmpdir.join('signal-converted.wav'))
        af.convert_to_wav(non_audio_file, converted_file)


@pytest.mark.parametrize("bit_depth", [8, 16, 24])
@pytest.mark.parametrize(
    'file_extension',
    ('wav', 'flac', 'ogg', 'mp3'),
)
def test_convert_to_wav(tmpdir, bit_depth, file_extension):
    sampling_rate = 8000
    channels = 1
    signal = sine(
        duration=0.1,
        sampling_rate=sampling_rate,
        channels=channels,
    )
    infile = str(tmpdir.join(f'signal.{file_extension}'))
    if file_extension == 'mp3':
        tmpfile = str(tmpdir.join('signal-tmp.wav'))
        af.write(tmpfile, signal, sampling_rate, bit_depth=bit_depth)
        convert_to_mp3(tmpfile, infile, sampling_rate, channels)
    else:
        af.write(infile, signal, sampling_rate, bit_depth=bit_depth)
    outfile = str(tmpdir.join('signal_converted.wav'))
    af.convert_to_wav(infile, outfile)
    converted_signal, converted_sampling_rate = af.read(outfile)
    assert converted_sampling_rate == sampling_rate
    if file_extension == 'mp3':
        assert af.bit_depth(outfile) == 16
        # Don't compare signals for MP3
        # as duration differs as well
    elif file_extension == 'ogg':
        assert af.bit_depth(outfile) == 16
        assert np.abs(converted_signal - signal).max() < 0.06
    elif file_extension in ['wav', 'flac']:
        assert af.bit_depth(outfile) == bit_depth
        assert np.abs(converted_signal - signal).max() < tolerance(bit_depth)


@pytest.mark.parametrize("bit_depth", [8, 16, 24, 32])
@pytest.mark.parametrize("duration", [0.01, 0.9999, 2])
@pytest.mark.parametrize("sampling_rate", [100, 8000, 44100])
@pytest.mark.parametrize("channels", [1, 2, 3, 10])
@pytest.mark.parametrize("always_2d", [False, True])
def test_wav(tmpdir, bit_depth, duration, sampling_rate, channels, always_2d):
    file = str(tmpdir.join('signal.wav'))
    signal = sine(duration=duration,
                  sampling_rate=sampling_rate,
                  channels=channels)
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
        atol=tolerance('duration', sampling_rate),
    )
    assert info.samplerate == sampling_rate
    assert info.channels == channels
    assert info.frames == samples
    # Compare with signal values to check read()
    assert_allclose(
        _duration(sig, fs),
        duration,
        rtol=0,
        atol=tolerance('duration', sampling_rate),
    )
    assert fs == sampling_rate
    assert _channels(sig) == channels
    assert _samples(sig) == samples
    # Test audiofile metadata methods
    assert_allclose(af.duration(file), duration,
                    rtol=0, atol=tolerance('duration', sampling_rate))
    assert af.sampling_rate(file) == sampling_rate
    assert af.channels(file) == channels
    assert af.samples(file) == samples
    assert af.bit_depth(file) == bit_depth
    # Test types of audiofile metadata methods
    assert type(af.duration(file)) is float
    assert type(af.sampling_rate(file)) is int
    assert type(af.channels(file)) is int
    assert type(af.samples(file)) is int
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
        assert _samples(sig) == int(np.ceil(duration * sampling_rate))


@pytest.mark.parametrize('magnitude', [0.01, 0.1, 1])
@pytest.mark.parametrize('normalize', [False, True])
@pytest.mark.parametrize('bit_depth', [16, 24, 32])
@pytest.mark.parametrize('sampling_rate', [44100])
def test_magnitude(tmpdir, magnitude, normalize, bit_depth, sampling_rate):
    file = str(tmpdir.join('signal.wav'))
    signal = sine(magnitude=magnitude, sampling_rate=sampling_rate)
    if normalize:
        magnitude = 1.0
    sig, _ = write_and_read(file, signal, sampling_rate, bit_depth=bit_depth,
                            normalize=normalize)
    assert_allclose(_magnitude(sig), magnitude,
                    rtol=0, atol=tolerance(bit_depth))
    assert type(_magnitude(sig)) is np.float32


@pytest.mark.parametrize('file_type', ['wav', 'flac', 'ogg'])
@pytest.mark.parametrize('sampling_rate', [8000, 48000])
@pytest.mark.parametrize("channels", [1, 2, 8, 255])
@pytest.mark.parametrize('magnitude', [0.01])
def test_file_type(tmpdir, file_type, magnitude, sampling_rate, channels):
    file = str(tmpdir.join('signal.' + file_type))
    signal = sine(
        magnitude=magnitude,
        sampling_rate=sampling_rate,
        channels=channels,
    )
    # Skip unallowed combination
    if file_type == 'flac' and channels > 8:
        return 0
    # Allowed combinations
    bit_depth = 16
    sig, fs = write_and_read(file, signal, sampling_rate, bit_depth=bit_depth)
    # Test file type
    assert audeer.file_extension(file) == file_type
    # Test magnitude
    assert_allclose(
        _magnitude(sig),
        magnitude,
        rtol=0,
        atol=tolerance(16),
    )
    # Test metadata
    info = soundfile.info(file)
    assert fs == sampling_rate
    assert info.samplerate == sampling_rate
    assert _channels(sig) == channels
    assert info.channels == channels
    assert _samples(sig) == _samples(signal)
    assert info.frames == _samples(signal)
    if file_type == 'ogg':
        bit_depth = None
    assert af.bit_depth(file) == bit_depth


@pytest.mark.parametrize('sampling_rate', [8000, 48000])
@pytest.mark.parametrize("channels", [1, 2])
@pytest.mark.parametrize('magnitude', [0.01])
def test_mp3(tmpdir, magnitude, sampling_rate, channels):

    signal = sine(magnitude=magnitude,
                  sampling_rate=sampling_rate,
                  channels=channels)
    # Create wav file and use ffmpeg to convert to mp3
    wav_file = str(tmpdir.join('signal.wav'))
    mp3_file = str(tmpdir.join('signal.mp3'))
    af.write(wav_file, signal, sampling_rate)
    convert_to_mp3(wav_file, mp3_file, sampling_rate, channels)
    assert audeer.file_extension(mp3_file) == 'mp3'
    sig, fs = af.read(mp3_file)
    assert fs == sampling_rate
    assert _channels(sig) == channels
    if channels == 1:
        assert sig.ndim == 1
    else:
        assert sig.ndim == 2
    assert af.channels(mp3_file) == _channels(sig)
    assert af.sampling_rate(mp3_file) == sampling_rate
    assert af.samples(mp3_file) == _samples(sig)
    assert af.duration(mp3_file) == _duration(sig, sampling_rate)
    assert_allclose(
        af.duration(mp3_file, sloppy=True),
        _duration(sig, sampling_rate),
        rtol=0,
        atol=0.2,
    )
    assert af.bit_depth(mp3_file) is None

    # Test additional arguments to read MP3 files
    offset = 0.1
    duration = 0.5
    sig, fs = af.read(mp3_file, offset=offset, duration=duration)
    assert _duration(sig, sampling_rate) == duration
    sig, fs = af.read(mp3_file, offset=offset)
    assert_allclose(
        _duration(sig, sampling_rate),
        af.duration(mp3_file) - offset,
        rtol=0,
        atol=tolerance('duration', sampling_rate),
    )


def test_formats():
    files = [
        'gs-16b-1c-44100hz.opus',
        'gs-16b-1c-8000hz.amr',
        'gs-16b-1c-44100hz.m4a',
        'gs-16b-1c-44100hz.aac',
    ]
    header_durations = [  # as given by mediainfo
        15.839,
        15.840000,
        15.833,
        None,
    ]
    files = [os.path.join(ASSETS_DIR, f) for f in files]
    for file, header_duration in zip(files, header_durations):
        signal, sampling_rate = af.read(file)
        assert af.channels(file) == _channels(signal)
        assert af.sampling_rate(file) == sampling_rate
        assert af.samples(file) == _samples(signal)
        duration = _duration(signal, sampling_rate)
        assert af.duration(file) == duration
        if header_duration is None:
            # Here we expect samplewise precision
            assert af.duration(file, sloppy=True) == duration
        else:
            # Here we expect limited precision
            # as the results differ between soxi and mediainfo
            precision = 1
            sloppy_duration = round(af.duration(file, sloppy=True), precision)
            header_duration = round(header_duration, precision)
            assert sloppy_duration == header_duration
        assert af.bit_depth(file) is None

        if file.endswith('m4a'):
            # Test additional arguments to read with ffmpeg
            offset = 0.1
            duration = 0.5
            sig, fs = af.read(file, offset=offset, duration=duration)
            assert _duration(sig, sampling_rate) == duration
            sig, fs = af.read(file, offset=offset)
            assert _duration(sig, sampling_rate) == af.duration(file) - offset


def test_write_errors():

    sampling_rate = 44100

    # Call with unallowed bit depths
    expected_error = '"bit_depth" has to be one of'
    with pytest.raises(RuntimeError, match=expected_error):
        af.write('test.wav', np.zeros((1, 100)), sampling_rate, bit_depth=1)

    # Checking for not allowed combinations of channel and file type
    expected_error = (
        "The maximum number of allowed channels "
        "for 'flac' is 8. Consider using 'wav' instead."
    )
    with pytest.raises(RuntimeError, match=expected_error):
        write_and_read('test.flac', np.zeros((9, 100)), sampling_rate)
    expected_error = (
        "The maximum number of allowed channels "
        "for 'ogg' is 255. Consider using 'wav' instead."
    )
    with pytest.raises(RuntimeError, match=expected_error):
        write_and_read('test.ogg', np.zeros((256, 100)), sampling_rate)
    expected_error = (
        "The maximum number of allowed channels "
        "for 'wav' is 65535."
    )
    with pytest.raises(RuntimeError, match=expected_error):
        write_and_read('test.wav', np.zeros((65536, 100)), sampling_rate)
