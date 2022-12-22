Changelog
=========

All notable changes to this project will be documented in this file.

The format is based on `Keep a Changelog`_,
and this project adheres to `Semantic Versioning`_.


Version 1.1.1 (2022-12-22)
--------------------------

* Added: support for Python 3.11
* Added: support for Python 3.10
* Changed: split API documentation into sub-pages
  for each function
* Removed: dependency on ``pysox``


Version 1.1.0 (2022-04-14)
--------------------------

* Changed: use ``ffmpeg`` or ``mediainfo``
  if ``sox`` binary is missing
  instead of raising an error
* Changed: improve ``FileNotFoundError`` message
  when ``ffmpeg`` or ``mediainfo`` are required,
  but not installed
* Fixed: always raise ``RuntimeError``
  for broken files or missing files
* Fixed: mention expected ``FileNotFoundError``
  when ``ffmpeg`` or ``mediainfo`` are required,
  but not installed
* Fixed: use ``soundfile``
  for converting WAV, FLAC, OGG files
  with ``audiofile.convert_to_wav()``


Version 1.0.3 (2022-01-03)
--------------------------

* Removed: Python 3.6 support


Version 1.0.2 (2021-12-06)
--------------------------

* Fixed: raise ``RuntimeError``
  for broken or empty non SND files


Version 1.0.1 (2021-10-28)
--------------------------

* Fixed: ``audiofile.duration()`` returns now ``0.0``
  for an empty WAV file with wrong file extension
  instead of ``None``


Version 1.0.0 (2021-08-05)
--------------------------

* Added: support for Python 3.9
* Added: tests for Windows
* Added: tests for macOS
* Added: ``sloppy`` argument to ``audiofile.duration()``
  for faster processing of non SND formats
* Changed: ``audiofile.write()`` raises ``RuntimeError``
  instead of ``SystemExit``
* Changed: added ``sloppy=True`` results
  when accessing metadata of MP3 and MP4 files in the benchmarks
* Removed: deprecated precision argument from ``audiofile.write()``


Version 0.4.3 (2021-07-30)
--------------------------

* Fixed: make ``dtype`` keyword argument available in ``audiofile.read()``


Version 0.4.2 (2021-04-26)
--------------------------

* Fixed: allow for ``duration=0.0`` in ``audiofile.read()``


Version 0.4.1 (2020-12-17)
--------------------------

* Added: ``bit_depth`` to usage section of documentation
* Fixed: handling of file names that include ``~`` or ``..``
  by using ``audeer.safe_path``


Version 0.4.0 (2020-11-26)
--------------------------

* Added ``audiofile.bit_depth()``
  which returns bit depth of WAV and FLAC files
* Added: ``bit_depth`` argument to ``audiofile.write()``
* Deprecated: ``precision`` argument of ``audiofile.write()``,
  use ``bit_depth`` instead


Version 0.3.4 (2020-10-29)
--------------------------

* Fixed: several typos in the documentation


Version 0.3.3 (2020-10-29)
--------------------------

* Added: more tests to increase code coverage to 100%
* Added: link to benchmark page in README
* Changed: tests now require 100% code coverage


Version 0.3.2 (2020-10-29)
--------------------------

* Added: benchmark results page in docs
* Fixed: multi-line release changelogs on Github
* Fixed: copy-button for bash examples


Version 0.3.1 (2020-10-27)
--------------------------

* Fixed: missing dependencies for publishing documentation


Version 0.3.0 (2020-10-27)
--------------------------

* Changed: use ``audiofile.core`` structure under the hood
* Changed: use Github Actions for tests
* Changed: use Github Actions for automatic publishing
* Changed: host documentation as Github pages
* Removed: support for Python 2.7


Version 0.2.4 (2020-08-31)
--------------------------

* Fixed: ``CHANGELOG`` format for PyPI server


Version 0.2.3 (2020-08-31)
--------------------------

* Fixed: catch ``SoxiError`` in ``audiofile.read()``
* Fixed: test for more advanced audio files like OPUS, AMR, ...


Version 0.2.2 (2019-10-04)
--------------------------

* Changed: switch to keep a changelog format
* Changed: define package in ``setup.cfg``


Version 0.2.1 (2019-05-02)
--------------------------

* Fixed: module only package


Version 0.2.0 (2019-05-02)
--------------------------

* Changed: improve documentation
* Changed: switch to single ``audiofile.py`` module
* Fixed: skip tests if download fails


Version 0.1.3 (2019-03-27)
--------------------------

* Fixed: metadata samples and duration for MP3 files


Version 0.1.2 (2019-03-25)
--------------------------

* Fixed: metadata for pypi.org


Version 0.1.1 (2019-03-25)
--------------------------

* Fixed: license statement in PyPI package


Version 0.1.0 (2019-03-25)
--------------------------

* Added: First public release


.. _Keep a Changelog: https://keepachangelog.com/en/1.0.0/
.. _Semantic Versioning: https://semver.org/spec/v2.0.0.html
