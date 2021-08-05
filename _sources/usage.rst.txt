Usage
=====

:mod:`audiofile` can read and get metadata information
for all files that are supported by
ffmpeg_,
sox_,
and mediainfo_,
if those are available on your system.
In addition, it can create WAV, FLAC, or OGG files.


Write a file
------------

First,
let's create a dummy signal containing noise:

.. jupyter-execute::

    import audiofile
    import numpy as np

    sampling_rate = 8000  # in Hz
    noise = np.random.normal(0, 1, sampling_rate)
    noise /= np.amax(np.abs(noise))
    audiofile.write('noise.flac', noise, sampling_rate)


File information
----------------

Now you can get metadata information on that signal:

.. jupyter-execute::

    audiofile.channels('noise.flac')

.. jupyter-execute::

    audiofile.duration('noise.flac')

.. jupyter-execute::

    audiofile.samples('noise.flac')

.. jupyter-execute::

    audiofile.sampling_rate('noise.flac')

.. jupyter-execute::

    audiofile.bit_depth('noise.flac')


Read a file
-----------

You can read the signal:

.. jupyter-execute::

    sig, fs = audiofile.read('noise.flac')
    print(f'sampling rate: {fs}, signal shape: {sig.shape}')

If you prefer a workflow
that returns a 2D signal with channel as the first dimension,
enforce it with:

.. jupyter-execute::

    sig, fs = audiofile.read('noise.flac', always_2d=True)
    print(f'sampling rate: {fs}, signal shape: {sig.shape}')

If you just want to read from 500 ms to 900 ms of the signal:

.. jupyter-execute::

    sig, fs = audiofile.read('noise.flac', offset=0.5, duration=0.4)
    print(f'sampling rate: {fs}, signal shape: {sig.shape}')


Convert a file
--------------

You can convert any file to WAV using:

.. jupyter-execute::

    audiofile.convert_to_wav('noise.flac', 'noise.wav')
    audiofile.samples('noise.wav')


.. jupyter-execute::
    :hide-code:
    :hide-output:

    import os
    os.remove('noise.wav')
    os.remove('noise.flac')


.. _soundfile: https://pysoundfile.readthedocs.io/
.. _ffmpeg: https://www.ffmpeg.org/
.. _sox: http://sox.sourceforge.net/
.. _mediainfo: https://mediaarea.net/en/MediaInfo/
