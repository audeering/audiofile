=========
audiofile
=========

|tests| |coverage| |docs| |python-versions| |license|

The Python package **audiofile** handles all kind of audio files
with a focus on reading speed.

It can read and get metadata information
for all files that are supported by
ffmpeg_,
sox_,
and mediainfo_,
if those are available on your system.
In addition, it can create WAV files.

Code example for reading a file:

.. code-block:: python

    import audiofile as af

    signal, sampling_rate = af.read('signal.wav')


.. _virtualenv: https://virtualenv.pypa.io/
.. _ffmpeg: https://www.ffmpeg.org/
.. _sox: http://sox.sourceforge.net/
.. _mediainfo: https://mediaarea.net/en/MediaInfo/

.. |tests| image:: https://github.com/audeering/audiofile/workflows/Test/badge.svg
    :target: https://github.com/audeering/audiofile/actions?query=workflow%3ATest
    :alt: Test status
.. |coverage| image:: https://codecov.io/gh/audeering/audiofile/branch/master/graph/badge.svg?token=LVF0621BKR
    :target: https://codecov.io/gh/audeering/audiofile/
    :alt: code coverage
.. |docs| image:: https://readthedocs.org/projects/audiofile/badge/
    :target: https://audiofile.readthedocs.io/
    :alt: audiofile's documentation on Read the Docs
.. |python-versions| image:: https://img.shields.io/pypi/pyversions/audiofile.svg
    :target: https://pypi.org/project/audiofile/
    :alt: audiofile's supported Python versions
.. |license| image:: https://img.shields.io/badge/license-MIT-green.svg
    :target: https://github.com/audeering/audiofile/blob/master/LICENSE
    :alt: audiofile's MIT license
