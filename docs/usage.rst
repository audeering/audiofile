Usage
=====

Import the package and use it to write or read an audio file,
or get information about its metadata:

.. code-block:: python

    import numpy as np
    import audiofile as af

    sampling_rate = 8000  # in Hz
    noise = np.random.normal(0, 1, sampling_rate)
    noise /= np.amax(np.abs(noise))
    af.write('noise.wav', noise, sampling_rate)
    af.channels('noise.wav')
    af.duration('noise.wav')
    sig, fs = af.read('noise.wav')

It should work with every audio file you will work with.
WAV, FLAC, and OGG files are handled by soundfile_.
The reading of all other audio files
is managed by converting them to a temporary WAV file
by pysox_ or ffmpeg_,
which means it can handle audio from video files as well.

.. _soundfile: https://pysoundfile.readthedocs.io/
.. _pysox: http://pysox.readthedocs.org/
.. _ffmpeg: https://www.ffmpeg.org/
