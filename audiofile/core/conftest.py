import os

import numpy as np
import pytest

import audeer
import audiofile


np.random.seed(1)


@pytest.fixture(scope='session', autouse=True)
def audio_file():
    # Create an audio file to be used in doctests
    sampling_rate = 8000
    mono_wav_file = audeer.path('mono.wav')
    stereo_wav_file = audeer.path('stereo.wav')
    stereo_flac_file = audeer.path('stereo.flac')
    signal = np.random.uniform(-1, 1, (1, 1000))
    audiofile.write(mono_wav_file, signal, sampling_rate)
    signal = np.random.uniform(-1, 1, (2, 1000))
    audiofile.write(stereo_wav_file, signal, sampling_rate)
    audiofile.write(stereo_flac_file, signal, sampling_rate)

    yield

    # Clean up
    for file in [
            mono_wav_file,
            stereo_wav_file,
            stereo_flac_file,
    ]:
        if os.path.exists(file):
            os.remove(file)
