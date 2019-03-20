"""Read, write, and get information about audio files."""
from __future__ import division
import os
import sys
import logging
import subprocess
from shlex import split
try:
    from tempfile import TemporaryDirectory
except ImportError:  # Python 2.7
    from backports.tempfile import TemporaryDirectory

import numpy as np
import soundfile
import sox


# File formats handled by soundfile
SNDFORMATS = ['wav', 'flac', 'ogg']
# Disable warning outputs of sox as we use it with try
logging.getLogger('sox').setLevel(logging.CRITICAL)


def write(file,
          signal,
          sampling_rate,
          precision='16bit',
          normalize=False,
          **kwargs):
    """Write (normalized) audio files.

    Save audio data provided as an array of shape `[channels, samples]` to a
    WAV, FLAC, or OGG file. `channels` can be up to 65535 for WAV, 255 for OGG,
    and 8 for FLAC. For monaural audio the array can be one-dimensional.

    It uses soundfile to write the audio files.

    Args:
        file (str or int or file-like object): file name of output audio file.
            The format (WAV, FLAC, OGG) will be inferred from the file name
        signal (numpy.ndarray): audio data to write
        sampling_rate (int): sample rate of the audio data
        precision (str, optional): precision of writen file, can be `'16bit'`,
            `'24bit'`, `'32bit'`. Only available for WAV files.
            Default: `16bit`
        normalize (bool, optional): normalize audio data before writing.
            Default: `False`
        kwargs: pass on further arguments to :py:func:`soundfile.write`

    Note:
        OGG file handling will not work properly under Ubuntu 16.04 due to a
        bug in its libsndfile version.

    """
    precision_mapping = {
        '16bit': 'PCM_16',
        '24bit': 'PCM_24',
        '32bit': 'PCM_32',
    }
    max_channels = {
        'wav': 65535,
        'ogg': 255,
        'flac': 8,
    }
    # Check for allowed precisions
    allowed_precissions = sorted(list(precision_mapping.keys()))
    if precision not in allowed_precissions:
        sys.exit('"precision" has to be one of {}.'
                 .format(', '.join(allowed_precissions)))
    # Check if number of channels is allowed for chosen file type
    file_type = _file_extension(file)
    if signal.ndim > 1:
        channels = np.shape(signal)[0]
    else:
        channels = 1
    if channels > max_channels[file_type]:
        if file_type != 'wav':
            hint = 'Consider using "wav" instead.'
        sys.exit('The maximum number of allowed channels for {} is '
                 '{}. {}'.format(file_type, max_channels[file_type], hint))
    # Precision setting is only available for WAV files
    if file_type == 'wav':
        subtype = precision_mapping[precision]
    else:
        subtype = None
    if normalize:
        signal = signal / np.max(np.abs(signal))
    soundfile.write(file, signal.T, sampling_rate, subtype=subtype, **kwargs)


def read(file, duration=None, offset=0, always_2d=False, **kwargs):
    """Read audio file.

    It uses soundfile for WAV, FLAC, and OGG files. All other audio files are
    first converted to WAV by sox or ffmpeg.

    Args:
        file (str or int or file-like object): file name of input audio file
        duration (float, optional): return only a specified duration in
            seconds. Default: `None`
        offset (float, optional): start reading at offset in seconds.
            Default: `0`
        always_2d (bool, optional): if `True` it always returns a
            two-dimensional signal even for mono sound files. Default: `False`
        kwargs: pass on further arguments to :py:func:`soundfile.read`

    Returns:
        (tuple):

            * **numpy.ndarray**: a two-dimensional array in the form
              `[channels, samples]`. If the sound file has only one channel,
              a one-dimensional array is returned
            * **int**: sample rate of the audio file

    Note:
        OGG file handling will not work properly under Ubuntu 16.04 due to a
        bug in its libsndfile version.

    """
    tmpdir = None
    if _file_extension(file) not in SNDFORMATS:
        # Convert file formats not recognized by soundfile to WAV first.
        #
        # NOTE: this is faster than loading them with librosa directly.
        # In addition, librosa seems to have an issue with the precission of
        # the returned magnitude
        # (https://github.com/librosa/librosa/issues/811).
        #
        # It might be the case that MP3 files will be supported by soundfile in
        # the future as well. For a discussion on MP3 support in the underlying
        # libsndfile see https://github.com/erikd/libsndfile/issues/258.
        with TemporaryDirectory(prefix='audiofile') as tmpdir:
            tmpfile = os.path.join(tmpdir, 'tmp.wav')
            convert_to_wav(file, tmpfile, offset, duration)
            signal, sample_rate = soundfile.read(tmpfile, dtype='float32',
                                                 always_2d=always_2d, **kwargs)
    else:
        if duration or offset > 0:
            sample_rate = sampling_rate(file)
        if offset > 0:
            offset = np.ceil(offset * sample_rate)  # samples
        if duration:
            duration = int(np.ceil(duration * sample_rate) + offset)  # samples
        signal, sample_rate = soundfile.read(file, start=int(offset),
                                             stop=duration, dtype='float32',
                                             always_2d=always_2d, **kwargs)
    # [samples, channels] => [channels, samples]
    signal = signal.T
    return signal, sample_rate


def duration(file):
    """Duration in seconds of audio file.

    Args:
        file (str or int or file-like object): file name of input audio file

    Returns:
        float: duration in seconds of audio file

    """
    if _file_extension(file) in SNDFORMATS:
        return soundfile.info(file).duration
    else:
        try:
            return sox.file_info.duration(file)
        except sox.core.SoxiError:
            return samples(file) / sampling_rate(file)


def samples(file):
    """Number of samples in audio file (0 if unavailable).

    Args:
        file (str or int or file-like object): file name of input audio file

    Returns:
        int: number of samples in audio file

    """
    if _file_extension(file) in SNDFORMATS:
        return int(soundfile.info(file).duration
                   * soundfile.info(file).samplerate)
    else:
        try:
            return sox.file_info.num_samples(file)
        except sox.core.SoxiError:
            with TemporaryDirectory(prefix='audiofile') as tmpdir:
                tmpfile = os.path.join(tmpdir, 'tmp.wav')
                convert_to_wav(file, tmpfile)
                return int(soundfile.info(tmpfile).duration
                           * soundfile.info(tmpfile).samplerate)


def channels(file):
    """Number of channels in audio file.

    Args:
        file (str or int or file-like object): file name of input audio file

    Returns:
        int: number of channels in audio file

    """
    if _file_extension(file) in SNDFORMATS:
        return soundfile.info(file).channels
    else:
        try:
            return int(sox.file_info.channels(file))
        except sox.core.SoxiError:
            # For MP4 stored and returned number of channels can be different
            cmd1 = ('mediainfo --Inform="Audio;%Channel(s)_Original%" {}'
                    .format(file))
            cmd2 = 'mediainfo --Inform="Audio;%Channel(s)%" {}'.format(file)
            try:
                return int(_run(cmd1))
            except ValueError:
                return int(_run(cmd2))


def sampling_rate(file):
    """Sampling rate of audio file.

    Args:
        file (str or int or file-like object): file name of input audio file

    Returns:
        int: sampling rate of audio file

    """
    if _file_extension(file) in SNDFORMATS:
        return soundfile.info(file).samplerate
    else:
        try:
            return int(sox.file_info.sample_rate(file))
        except sox.core.SoxiError:
            cmd = 'mediainfo --Inform="Audio;%SamplingRate%" {}'.format(file)
            return int(_run(cmd))


def convert_to_wav(infile, outfile, offset=0, duration=None):
    """Convert any audio/video file to WAV.

    It uses sox or ffmpeg for the conversion.
    If `duration` and/or `offset` are specified the resulting WAV file will be
    shorter accordingly to those values.

    Args:
        infile (str): audio/video file name
        outfile (str): WAV file name
        duration (float, optional): return only a specified duration in
            seconds. Default: `None`
        offset (float, optional): start reading at offset in seconds.
            Default: `0`

    """
    try:
        # Convert to WAV file with sox
        _sox(infile, outfile, offset, duration)
    except sox.core.SoxError:
        # Convert to WAV file with ffmpeg
        _ffmpeg(infile, outfile, offset, duration)


def _sox(infile, outfile, offset, duration):
    """Convert audio file to WAV file."""
    tfm = sox.Transformer()
    if duration:
        tfm.trim(offset, duration + offset)
    elif offset > 0:
        tfm.trim(offset)
    tfm.build(infile, outfile)


def _ffmpeg(infile, outfile, offset, duration):
    """Convert audio file to WAV file."""
    if duration:
        cmd = ('ffmpeg -ss {} -i "{}" -t {} "{}"'
               .format(offset, infile, duration, outfile))
    else:
        cmd = 'ffmpeg -ss {} -i "{}" "{}"'.format(offset, infile, outfile)
    _run(cmd)


def _file_extension(path):
    """Lower case file extension."""
    return os.path.splitext(path)[-1][1:].lower()


def _run(shell_command):
    """Return the output of a shell command provided as string."""
    out = subprocess.check_output(split(shell_command),
                                  stderr=subprocess.STDOUT).split()
    try:
        return out[0]
    except IndexError:
        return ''
