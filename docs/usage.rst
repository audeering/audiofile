Usage
=====

:mod:`audiofile` can read and get metadata information
for all files that are supported by
ffmpeg_,
sox_,
and mediainfo_,
if those are available on your system.
In addition, it can create WAV, FLAC, MP3, or OGG files.


Write a file
------------

First,
let's create a dummy signal containing noise:

.. code-block:: python

    import audiofile
    import numpy as np

    sampling_rate = 8000  # in Hz
    noise = np.random.normal(0, 1, sampling_rate)
    noise /= np.amax(np.abs(noise))
    audiofile.write("noise.flac", noise, sampling_rate)


File information
----------------

Now you can get metadata information on that signal:

>>> audiofile.channels("noise.flac")
1
>>> audiofile.duration("noise.flac")
1.0
>>> audiofile.samples("noise.flac")
8000
>>> audiofile.sampling_rate("noise.flac")
8000
>>> audiofile.bit_depth("noise.flac")
16


Read a file
-----------

You can read the signal:

>>> signal, sampling_rate = audiofile.read("noise.flac")
>>> sampling_rate
8000
>>> signal.shape
(8000,)

If you prefer a workflow
that returns a 2D signal with channel as the first dimension,
enforce it with:

>>> signal, sampling_rate = audiofile.read("noise.flac", always_2d=True)
>>> signal.shape
(1, 8000)

If you just want to read from 500 ms to 900 ms of the signal:

>>> signal, sampling_rate = audiofile.read("noise.flac", offset=0.5, duration=0.4)
>>> signal.shape
(3200,)


Convert a file
--------------

You can convert any file to WAV using:

>>> import audeer
>>> wav_file = audiofile.convert_to_wav("noise.flac", "noise.wav")


Resample/Remix a file
---------------------

:mod:`audiofile` does not directly support
resampling or remixing
of an audio file
during reading.
But it can be easily achieved with :mod:`audresample`.

>>> import audresample
>>> target_rate = 16000
>>> signal, sampling_rate = audiofile.read("noise.flac", always_2d=True)
>>> signal = audresample.resample(signal, sampling_rate, target_rate)
>>> signal = audresample.remix(signal, channels=[0, 0])
>>> audiofile.write("noise-remix.flac", signal, target_rate)
>>> audiofile.sampling_rate('noise-remix.flac')
16000
>>> signal.shape
(2, 16000)


.. _soundfile: https://python-soundfile.readthedocs.io/
.. _ffmpeg: https://www.ffmpeg.org/
.. _sox: https://sourceforge.net/projects/sox/
.. _mediainfo: https://mediaarea.net/en/MediaInfo/
