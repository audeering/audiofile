=========
audiofile
=========

|tests| |docs|

The python package ``audiofile`` provides a meta package to handle all kind of
audio files under Python with a focus on reading speed.

Documentation: https://audiofile.readthedocs.io/

.. |tests| image::
    https://travis-ci.com/hagenw/audiofile.svg?token=fZTrhos7q5jTzFhs65MQ&branch=master
        :target: https://travis-ci.com/hagenw/audiofile
.. |docs| image:: https://readthedocs.org/projects/audiofile/badge/

Installation
============

It is recommended to first create a Python virtual environment using a tool like
virtualenv_, e.g.

.. code-block:: bash

    virtualenv --python=/usr/bin/python3 --no-site-packages _env
    source _env/bin/activate

Afterwards install ``audiofile`` with

.. code-block:: bash
    
    pip install audiofile

In order to handle all possible audio files, please make sure ffmpeg_ and
mediainfo_ are installed on your system.

If you want to use Python 2.7 make sure you install the following backports
package as well:

.. code-block:: bash

    pip install backports.tempfile

.. _virtualenv: https://virtualenv.pypa.io/
.. _ffmpeg: https://www.ffmpeg.org/
.. _mediainfo: https://mediaarea.net/en/MediaInfo/

Usage
=====

Import the package and use it to write or read an audio file, or get information
about its metadata:

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

It should work with every audio file you will work with. WAV, FLAC, and OGG
files are handled by soundfile_. The reading of all other audio files is managed
by converting them to a temporary WAV file by pysox_ or ffmpeg_, which means it
can handle audio from video files as well.

.. _soundfile: https://pysoundfile.readthedocs.io/
.. _pysox: http://pysox.readthedocs.org/
.. _ffmpeg: https://www.ffmpeg.org/
