import sys
import os
from subprocess import check_output
from datetime import datetime


# Project -----------------------------------------------------------------

project = 'audiofile'
copyright = '2018-{} audEERING GmbH'.format(datetime.now().year)
author = 'Hagen Wierstorf'
# The x.y.z version read from tags
try:
    version = check_output(['git', 'describe', '--tags', '--always'])
    version = version.decode().strip()
except Exception:
    version = '<unknown>'
title = '{} Documentation'.format(project)


# General -----------------------------------------------------------------

master_doc = 'index'
extensions = []
source_suffix = '.rst'
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']
pygments_style = None
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.napoleon',  # support for Google-style docstrings
    'sphinx.ext.viewcode',
    'sphinx.ext.intersphinx',
]

intersphinx_mapping = {
    'python': ('https://docs.python.org/3/', None),
    'numpy': ('https://docs.scipy.org/doc/numpy/', None),
    'soundfile': ('https://pysoundfile.readthedocs.io/en/latest/', None),
}


# HTML --------------------------------------------------------------------

html_theme = 'sphinx_rtd_theme'
html_theme_options = {
    'display_version': True,
    'logo_only': False,
}
html_title = title


# LaTeX -------------------------------------------------------------------

latex_elements = {
    'papersize': 'a4paper',
}

# Grouping the document tree into LaTeX files. List of tuples
# (source start file, target name, title,
#  author, documentclass [howto, manual, or own class]).
latex_documents = [
    (master_doc, '{}-{}.tex'.format(project, version),
     title, author, 'manual'),
]


# Build dependencies
# Fake imports to avoid actually loading libsndfile
sys.path.insert(0, os.path.abspath('.'))
import fake__soundfile
sys.modules['_soundfile'] = sys.modules['fake__soundfile']
