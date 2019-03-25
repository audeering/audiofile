from setuptools import setup, find_packages
from io import open


def read_file(file_name):
    with open(file_name, encoding="utf-8") as stream:
        return stream.read().split("\n")[:-1]


readme = read_file('README.rst')
description = readme[1]
long_description = '\n'.join(readme)

setup(
    name='audiofile',
    packages=find_packages(),
    use_scm_version=True,
    setup_requires=['setuptools_scm'],
    install_requires=[
        'numpy',
        'soundfile',
        'sox',
    ],
    author='Hagen Wierstorf',
    author_email='hwierstorf@audeering.com',
    description=description,
    long_description_content_type='text/x-rst',
    license='MIT',
    keywords=['audio tools'],
    url='',
    platforms='any',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Topic :: Scientific/Engineering',
    ],
)
