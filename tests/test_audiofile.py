from __future__ import division
import os
import subprocess
import socket
import warnings

import pytest
import numpy as np
from numpy.testing import assert_allclose
import sox
from six.moves import urllib

import audiofile as af


def tolerance(condition, sampling_rate=0):
    """Absolute tolerance for different condition."""
    tol = 0
    if condition == 16:
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


def download_url(url, root):
    """Download a file from an url to a specified directory."""
    filename = os.path.basename(url)
    fpath = os.path.join(root, filename)
    if not os.path.isfile(fpath):
        urllib.request.urlretrieve(url, fpath)
    return fpath


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


def test_deprecated_precision(tmpdir):
    sampling_rate = 8000
    precision = '16bit'
    bit_depth = 16
    signal = sine(sampling_rate=sampling_rate)
    file = str(tmpdir.join('signal-precision.wav'))
    with warnings.catch_warnings(record=True) as w:
        af.write(file, signal, sampling_rate, precision)
        assert issubclass(w[-1].category, UserWarning)
        assert str(w[-1].message) == (
            f'Use "{bit_depth}" instead of '
            f'"{precision}" for specifying bit depth. '
            f'This will raise an error in version >=0.5.0'
        )
    with warnings.catch_warnings(record=True) as w:
        af.write(file, signal, sampling_rate, precision=precision)
        assert issubclass(w[-1].category, UserWarning)
        assert str(w[-1].message) == (
            f'Use "bit_depth={bit_depth}" '
            f'instead of "precision={precision}" '
            f'for specifying bit depth. '
            f'This will raise an error in version >=0.5.0'
        )


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
    # Compare with sox implementation to check write()
    assert_allclose(sox.file_info.duration(file), duration,
                    rtol=0, atol=tolerance('duration', sampling_rate))
    assert sox.file_info.sample_rate(file) == sampling_rate
    assert sox.file_info.channels(file) == channels
    assert sox.file_info.num_samples(file) == samples
    assert sox.file_info.bitdepth(file) == bit_depth
    # Compare with signal values to check read()
    assert_allclose(_duration(sig, fs), duration,
                    rtol=0, atol=tolerance('duration', sampling_rate))
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

    # Call with unallowed bit depths
    if sampling_rate == 100 and duration == 2 and channels == 1:
        expected_error = '"bit_depth" has to be one of'
        with pytest.raises(SystemExit, match=expected_error):
            af.write(file, signal, sampling_rate, bit_depth=1)


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
    signal = sine(magnitude=magnitude,
                  sampling_rate=sampling_rate,
                  channels=channels)
    # Checking for not allowed combinations of channel and file type
    if file_type == 'flac' and channels > 8:
        with pytest.raises(SystemExit):
            write_and_read(file, signal, sampling_rate)
        return 0
    # Allowed combinations
    sig, fs = write_and_read(file, signal, sampling_rate)
    # Test file type
    if file_type == 'ogg':
        file_type = 'vorbis'
    assert sox.file_info.file_type(file) == file_type
    # Test magnitude
    assert_allclose(_magnitude(sig), magnitude,
                    rtol=0, atol=tolerance(16))
    # Test sampling rate
    assert fs == sampling_rate
    assert sox.file_info.sample_rate(file) == sampling_rate
    # Test channels
    assert _channels(sig) == channels
    assert sox.file_info.channels(file) == channels
    # Test samples
    assert _samples(sig) == _samples(signal)
    assert sox.file_info.num_samples(file) == _samples(signal)
    # Test bit depth
    assert sox.file_info.bitdepth(file) == af.bit_depth(file)


@pytest.mark.parametrize('sampling_rate', [8000, 48000])
@pytest.mark.parametrize("channels", [1, 2])
@pytest.mark.parametrize('magnitude', [0.01])
def test_mp3(tmpdir, magnitude, sampling_rate, channels):
    signal = sine(magnitude=magnitude,
                  sampling_rate=sampling_rate,
                  channels=channels)
    # Create wav file and use sox to convert to mp3
    wav_file = str(tmpdir.join('signal.wav'))
    mp3_file = str(tmpdir.join('signal.mp3'))
    af.write(wav_file, signal, sampling_rate)
    subprocess.call(['sox', wav_file, mp3_file])
    assert sox.file_info.file_type(mp3_file) == 'mp3'
    sig, fs = af.read(mp3_file)
    assert_allclose(_magnitude(sig), magnitude,
                    rtol=0, atol=tolerance(16))
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
    assert af.bit_depth(mp3_file) is None

    # Test additional arguments to read with sox
    offset = 0.1
    duration = 0.5
    sig, fs = af.read(mp3_file, offset=offset, duration=duration)
    assert _duration(sig, sampling_rate) == duration
    sig, fs = af.read(mp3_file, offset=offset)
    # Don't test for 48000 Hz and 2 channels
    # https://github.com/audeering/audiofile/issues/23
    if not (sampling_rate == 48000 and channels == 2):
        assert_allclose(
            _duration(sig, sampling_rate),
            af.duration(mp3_file) - offset,
            rtol=0,
            atol=tolerance('duration', sampling_rate),
        )


def test_formats(tmpdir):
    base_url = 'https://dl.espressif.com/dl/audio/'
    files = [
        'gs-16b-1c-44100hz.opus',
        'gs-16b-1c-8000hz.amr',
        'gs-16b-1c-44100hz.m4a',
        'gs-16b-1c-44100hz.aac',
    ]
    urls = [base_url + f for f in files]
    for url in urls:
        print(url)
        try:
            file = download_url(url, str(tmpdir))
        except (urllib.error.ContentTooShortError,
                urllib.error.HTTPError,
                socket.gaierror):
            pytest.skip("Skip unavailable file")
        signal, sampling_rate = af.read(file)
        assert af.channels(file) == _channels(signal)
        assert af.sampling_rate(file) == sampling_rate
        assert af.samples(file) == _samples(signal)
        assert af.duration(file) == _duration(signal, sampling_rate)
        assert af.bit_depth(file) is None

        if url.endswith('m4a'):
            # Test additional arguments to read with ffmpeg
            offset = 0.1
            duration = 0.5
            sig, fs = af.read(file, offset=offset, duration=duration)
            assert _duration(sig, sampling_rate) == duration
            sig, fs = af.read(file, offset=offset)
            assert _duration(sig, sampling_rate) == af.duration(file) - offset
