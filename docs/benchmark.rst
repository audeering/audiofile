Benchmark
=========

We benchmarked several Python audio reading libraries
against each other.
The procedure follows the `python_audio_loading_benchmark project`_.


Procedure
---------

The benchmark loads 30 single channel audio files
and measures the time until the audio is converted
to a :class:`numpy.array`.

Audio files
^^^^^^^^^^^

All files have a sampling rate pf 44100 Hz.
They differ in length,
with 10 files have a length of 1 second,
10 files a length of 10 seconds,
and 10 files a length of 151 seconds.
All non WAV files were generated using ffmpeg_.

Python packages
^^^^^^^^^^^^^^^

The following Python packages are benchmarked against each other:

* aubio_
* audioread_
* :mod:`audiofile`
* librosa_
* scipy_
* soundfile_
* sox_

scipy_ and librosa_ are only tested for reading files,
whereas sox_ is only tested for accessing metadata information.
audioread_ can use three different libraries under the hood:
ffmpeg, gstreamer, mad.
All three are benchmarked,
but results are only reported for the best one.

Reading files
^^^^^^^^^^^^^

The benchmark loads the audio files
and measures the time until the audio is converted
to a :class:`numpy.array`.

Accessing metadata
^^^^^^^^^^^^^^^^^^

For benchmark accessing metadata information,
the following was requested for every file:

* channels
* duration
* samples
* sampling rate

Running the benchmark
^^^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

    $ cd docs/benchmark/
    $ bash generate_audiofiles.sh
    $ # Install dependencies for building wheels
    $ sudo apt-get install -y libcairo2-dev libmad0-dev libgirepository1.0-dev
    $ # Create and activate Python virtual environment, e.g.
    $ # virtualenv --no-download --python=python3 ${HOME}/.envs/audiofile-benchmark
    $ # source ${HOME}/.envs/audiofile-benchmark/bin/activate
    $ pip install -r requirements.txt
    $ bash run.sh


WAV, FLAC, OGG
--------------

Reading files
^^^^^^^^^^^^^


Accessing metadata
^^^^^^^^^^^^^^^^^^

sox_ and audioread_ have been removed from the results
as they were at least one magnitude slower.


MP3, MP4
--------

Not all libraries support these formats.

Reading files
^^^^^^^^^^^^^

Accessing metadata
^^^^^^^^^^^^^^^^^^


.. _aubio: https://github.com/aubio/aubio/
.. _audioread: https://github.com/beetbox/audioread/
.. _librosa: https://github.com/librosa/librosa/
.. _scipy: https://docs.scipy.org/doc/scipy/reference/generated/scipy.io.wavfile.read.html
.. _soundfile: https://github.com/bastibe/SoundFile/
.. _sox: https://github.com/rabitt/pysox/
.. _python_audio_loading_benchmark project: https://github.com/faroit/python_audio_loading_benchmark
