import configparser
from datetime import datetime
import shutil
import os

import audeer

config = configparser.ConfigParser()
config.read(os.path.join('..', 'setup.cfg'))


# Project -----------------------------------------------------------------

project = config['metadata']['name']
copyright = f'2018-{datetime.now().year} audEERING GmbH'
author = config['metadata']['author']
version = audeer.git_repo_version()
title = 'Documentation'


# General -----------------------------------------------------------------

master_doc = 'index'
extensions = []
source_suffix = '.rst'
exclude_patterns = [
    'build',
    'tests',
    'Thumbs.db',
    '.DS_Store',
    'api-src',
]
templates_path = ['_templates']
pygments_style = None
extensions = [
    'jupyter_sphinx',
    'sphinx.ext.autodoc',
    'sphinx.ext.autosummary',
    'sphinx.ext.napoleon',  # support for Google-style docstrings
    'sphinx_autodoc_typehints',
    'sphinx_copybutton',
    'sphinx.ext.viewcode',
    'sphinx.ext.intersphinx',
]

intersphinx_mapping = {
    'python': ('https://docs.python.org/3/', None),
    'numpy': ('https://docs.scipy.org/doc/numpy/', None),
    'soundfile': ('https://pysoundfile.readthedocs.io/en/latest/', None),
}

# Ignore package dependencies during building the docs
autodoc_mock_imports = ['soundfile']

copybutton_prompt_text = r'>>> |\.\.\. |\$ '
copybutton_prompt_is_regexp = True

# Disable auto-generation of TOC entries in the API
# https://github.com/sphinx-doc/sphinx/issues/6316
toc_object_entries = False


# HTML --------------------------------------------------------------------

html_theme = 'sphinx_audeering_theme'
html_theme_options = {
    'display_version': True,
    'footer_links': False,
    'logo_only': False,
}
html_context = {
    'display_github': True,
}
html_title = title


# Copy API (sub-)module RST files to docs/api/ folder ---------------------
audeer.rmdir('api')
audeer.mkdir('api')
api_src_files = audeer.list_file_names('api-src')
api_dst_files = [
    audeer.path('api', os.path.basename(src_file))
    for src_file in api_src_files
]
for src_file, dst_file in zip(api_src_files, api_dst_files):
    shutil.copyfile(src_file, dst_file)
