Contributing
============

If you would like to add new functionality fell free to create a
`pull request`_.
If you find errors, omissions, inconsistencies or other things that need
improvement, please create an issue_.
Contributions are always welcome!

.. _issue:
    https://github.com/audeering/audiofile/issues/new
.. _pull request:
    https://github.com/audeering/audiofile/compare

Development Installation
------------------------

Instead of pip-installing the latest release from PyPI_, you should get the
newest development version from Github_::

   git clone https://github.com/audeering/audiofile/
   cd audiofile
   # Create virtual environment, e.g.
   # virtualenv --python=/usr/bin/python3 --no-site-packages _env
   # source _env/bin/activate
   python setup.py develop

.. _PyPI: https://pypi.org/project/audiofile/
.. _Github: https://github.com/audeering/audiofile/

This way, your installation always stays up-to-date, even if you pull new
changes from the Github_ repository.

If you prefer, you can also replace the last command with::

   pip install -r requirements.txt

Building the Documentation
--------------------------

If you make changes to the documentation, you can re-create the HTML pages
using Sphinx_.
You can install it and a few other necessary packages with::

   pip install -r docs/requirements.txt

To create the HTML pages, use::

   python setup.py build_sphinx

The generated files will be available in the directory ``build/sphinx/html/``.

It is also possible to automatically check if all links are still valid::

   python setup.py build_sphinx -b linkcheck

.. _Sphinx: http://sphinx-doc.org/

Running the Tests
-----------------

You'll need pytest_ for that.
It can be installed with::

   pip install -r tests/requirements.txt

To execute the tests, simply run::

   python -m pytest

.. _pytest: https://pytest.org/

Creating a New Release
----------------------

New releases are made using the following steps:

#. Update ``CHANGELOG.rst``
#. Commit those changes as "Release X.Y.Z"
#. Create an (annotated) tag with ``git tag -a X.Y.Z``
#. Push the commit and the tag to Github
