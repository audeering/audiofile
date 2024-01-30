import os

import numpy as np
import pytest

import audeer

import audiofile


np.random.seed(1)


@pytest.fixture(scope="session", autouse=True)
def audio_file():
    create_audio_files(".")

    yield

    # Clean up
    for file in audeer.list_file_names(".", filetype="wav"):
        if os.path.exists(file):
            os.remove(file)
    for file in audeer.list_file_names(".", filetype="flac"):
        if os.path.exists(file):
            os.remove(file)


def create_audio_files(
    basedir,
):
    sampling_rate = 8000
    mono_wav_file = audeer.path(basedir, "mono.wav")
    stereo_wav_file = audeer.path(basedir, "stereo.wav")
    stereo_flac_file = audeer.path(basedir, "stereo.flac")
    signal = am_fm_synth(1.5, 1, sampling_rate)
    audiofile.write(mono_wav_file, signal, sampling_rate)
    signal = am_fm_synth(1.5, 2, sampling_rate)
    audiofile.write(stereo_wav_file, signal, sampling_rate)
    audiofile.write(stereo_flac_file, signal, sampling_rate)


def am_fm_synth(
    duration: float,
    num_channels: int = 1,
    sampling_rate: int = 16000,
    *,
    dtype: type = np.float32,
) -> np.ndarray:
    r"""Synthesise an AM/FM signal of given duration (sampled at given rate).

    Args:
        duration: duration in seconds
        num_channels: number of channels in the output signal
        sampling_rate: sampling rate in Hz
        dtype: data type

    Returns:
        Synthesised signal with shape `(number of channels, number of samples)`

    """
    n_samples = int(duration * sampling_rate)
    g = 0.8  # gain
    g_am = 0.7  # amount of AM
    f_am = 2.5  # frequency of AM (Hz)
    f0 = 0.04 * sampling_rate  # carrier frequency (Hz)
    f_mod = 2  # modulator frequency (Hz)
    f_dev = f0 * 0.95  # frequency deviation (intensity of FM)
    omega_am = 2 * np.pi * f_am / sampling_rate
    omega0_car = 2 * np.pi * f0 / sampling_rate
    omega_mod = 2 * np.pi * f_mod / sampling_rate
    omega_dev = 2 * np.pi * f_dev / sampling_rate
    ph_fm = 0  # initial phase of FM oscillator
    ph_am = np.pi / 2  # initial phase of AM oscillator
    sig = np.zeros((num_channels, n_samples), dtype=dtype)
    for ch_indx in range(num_channels):
        # No reinitialisation (to get true stereo)
        for t in range(n_samples):
            sig[ch_indx, t] = g * np.cos(ph_fm)
            sig[ch_indx, t] *= (1 - g_am) + g_am * np.square(np.cos(ph_am))
            ph_am += omega_am / 2
            ph_fm += omega0_car + omega_dev * np.cos(omega_mod * t)
    return sig
