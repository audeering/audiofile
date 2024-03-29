Installation
============

:mod:`audiofile` supports WAV, FLAC, MP3, OGG out of the box.
In order to handle other audio formats,
please make sure ffmpeg_,
mediainfo_,
and optionally sox_
are installed on your system.
e.g.

.. code-block:: bash

    $ sudo apt-get install ffmpeg mediainfo sox

To install :mod:`audiofile` run:

.. code-block:: bash

    $ # Create and activate Python virtual environment, e.g.
    $ # virtualenv --no-download --python=python3 ${HOME}/.envs/audiofile
    $ # source ${HOME}/.envs/audiofile/bin/activate
    $ pip install audiofile


.. _virtualenv: https://virtualenv.pypa.io/
.. _ffmpeg: https://www.ffmpeg.org/
.. _sox: http://sox.sourceforge.net/
.. _mediainfo: https://mediaarea.net/en/MediaInfo/
