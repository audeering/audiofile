=========
audiofile
=========

|tests| |coverage| |docs| |python-versions| |license|

The Python package **audiofile** handles all kind of audio files
with a focus on `reading speed`_.

It can read and request information
on channels, duration, number of samples and sampling rate
for all files that are supported by
ffmpeg_,
sox_,
and mediainfo_.
In addition,
it can write WAV, FLAC, and OGG files.

Have a look at the installation_ and usage_ instructions as a starting point.

Code example for reading a file:

.. code-block:: python

    import audiofile as af

    signal, sampling_rate = af.read('signal.wav')


.. _ffmpeg: https://www.ffmpeg.org/
.. _installation: https://audeering.github.io/audiofile/installation.html
.. _mediainfo: https://mediaarea.net/en/MediaInfo/
.. _usage: https://audeering.github.io/audiofile/usage.html
.. _reading speed: https://audeering.github.io/audiofile/benchmark.html
.. _sox: http://sox.sourceforge.net/
.. _virtualenv: https://virtualenv.pypa.io/

.. |tests| image:: https://github.com/audeering/audiofile/workflows/Test/badge.svg
    :target: https://github.com/audeering/audiofile/actions?query=workflow%3ATest
    :alt: Test status
.. |coverage| image:: https://codecov.io/gh/audeering/audiofile/branch/master/graph/badge.svg?token=LVF0621BKR
    :target: https://codecov.io/gh/audeering/audiofile/
    :alt: code coverage
.. |docs| image:: https://img.shields.io/pypi/v/audiofile?label=docs
    :target: https://audeering.github.io/audiofile/
    :alt: audiofile's documentation
.. |python-versions| image:: https://img.shields.io/pypi/pyversions/audiofile.svg
    :target: https://pypi.org/project/audiofile/
    :alt: audiofile's supported Python versions
.. |license| image:: https://img.shields.io/badge/license-MIT-green.svg
    :target: https://github.com/audeering/audiofile/blob/master/LICENSE
    :alt: audiofile's MIT license
