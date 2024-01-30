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

.. jupyter-execute::

    import audiofile
    import numpy as np

    sampling_rate = 8000  # in Hz
    noise = np.random.normal(0, 1, sampling_rate)
    noise /= np.amax(np.abs(noise))
    audiofile.write("noise.flac", noise, sampling_rate)


File information
----------------

Now you can get metadata information on that signal:

.. jupyter-execute::

    audiofile.channels("noise.flac")

.. jupyter-execute::

    audiofile.duration("noise.flac")

.. jupyter-execute::

    audiofile.samples("noise.flac")

.. jupyter-execute::

    audiofile.sampling_rate("noise.flac")

.. jupyter-execute::

    audiofile.bit_depth("noise.flac")


Read a file
-----------

You can read the signal:

.. jupyter-execute::

    signal, sampling_rate = audiofile.read("noise.flac")

    print(f"sampling rate: {sampling_rate}")
    print(f"signal shape: {signal.shape}")

If you prefer a workflow
that returns a 2D signal with channel as the first dimension,
enforce it with:

.. jupyter-execute::

    signal, sampling_rate = audiofile.read("noise.flac", always_2d=True)

    print(f"sampling rate: {sampling_rate}")
    print(f"signal shape: {signal.shape}")

If you just want to read from 500 ms to 900 ms of the signal:

.. jupyter-execute::

    signal, sampling_rate = audiofile.read("noise.flac", offset=0.5, duration=0.4)

    print(f"sampling rate: {sampling_rate}")
    print(f"signal shape: {signal.shape}")


Convert a file
--------------

You can convert any file to WAV using:

.. jupyter-execute::

    import audeer

    audiofile.convert_to_wav("noise.flac", "noise.wav")

    audeer.list_file_names(".", filetype="wav", basenames=True)


Resample/Remix a file
---------------------

:mod:`audiofile` does not directly support
resampling or remixing
of an audio file
during reading.
But it can be easily achieved with :mod:`audresample`.

.. jupyter-execute::

    import audresample

    target_rate = 16000
    signal, sampling_rate = audiofile.read("noise.flac", always_2d=True)
    signal = audresample.resample(signal, sampling_rate, target_rate)
    signal = audresample.remix(signal, channels=[0, 0])
    audiofile.write("noise-remix.flac", signal, target_rate)

    print(f"sampling rate: {audiofile.sampling_rate('noise-remix.flac')}")
    print(f"signal shape: {signal.shape}")


.. _soundfile: https://python-soundfile.readthedocs.io/
.. _ffmpeg: https://www.ffmpeg.org/
.. _sox: http://sox.sourceforge.net/
.. _mediainfo: https://mediaarea.net/en/MediaInfo/


.. Clean up
.. jupyter-execute::
    :hide-code:
    :hide-output:

    import os
    os.remove("noise.wav")
    os.remove("noise.flac")
    os.remove("noise-remix.flac")
