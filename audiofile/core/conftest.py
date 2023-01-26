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
    signal = np.random.uniform(-1, 1, (1, 1000))
    mono_file = audeer.path('mono.wav')
    audiofile.write('mono.wav', signal, sampling_rate)
    signal = np.random.uniform(-1, 1, (2, 1000))
    stereo_file = audeer.path('stereo.wav')
    audiofile.write(stereo_file, signal, sampling_rate)

    yield

    # Clean up
    if os.path.exists(mono_file):
        os.remove(mono_file)
    if os.path.exists(stereo_file):
        os.remove(stereo_file)
