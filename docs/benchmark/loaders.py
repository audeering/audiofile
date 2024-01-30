import audioread.ffdec
import audioread.gstdec
import audioread.maddec
import audioread.rawread
import librosa
import numpy as np
import pedalboard
from scipy.io import wavfile
import soundfile as sf
import sox

import audiofile as af


"""
Some of the code taken from:
https://github.com/aubio/aubio/blob/master/python/demos/demo_reading_speed.py
"""


def load_soundfile(fp):
    sig, rate = sf.read(fp)
    return sig


def load_scipy(fp):
    rate, sig = wavfile.read(fp)
    sig = sig.astype("float32") / 32767
    return sig


def load_scipy_mmap(fp):
    rate, sig = wavfile.read(fp, mmap=True)
    sig = sig.astype("float32") / 32767
    return sig


def load_ar_gstreamer(fp):
    with audioread.gstdec.GstAudioFile(fp) as f:
        total_frames = 0
        for buf in f:
            sig = _convert_buffer_to_float(buf)
            sig = sig.reshape(f.channels, -1)
            total_frames += sig.shape[1]
        return sig


def load_ar_mad(fp):
    with audioread.maddec.MadAudioFile(fp) as f:
        total_frames = 0
        for buf in f:
            sig = _convert_buffer_to_float(buf)
            sig = sig.reshape(f.channels, -1)
            total_frames += sig.shape[1]
        return sig


def load_ar_ffmpeg(fp):
    with audioread.ffdec.FFmpegAudioFile(fp) as f:
        total_frames = 0
        for buf in f:
            sig = _convert_buffer_to_float(buf)
            sig = sig.reshape(f.channels, -1)
            total_frames += sig.shape[1]
        return sig


def load_librosa(fp):
    # loading with `sr=None` is disabling the internal resampling
    sig, rate = librosa.load(fp, sr=None)
    return sig


def load_audiofile(fp):
    sig, rate = af.read(fp)
    return sig


def load_pedalboard(fp):
    with pedalboard.io.AudioFile(fp) as f:
        # Pedalboard output is (num_channels, num_samples)
        return f.read(f.frames)[0]


def _convert_buffer_to_float(buf, n_bytes=2, dtype=np.float32):
    # taken from librosa.util.utils
    # Invert the scale of the data
    scale = 1.0 / float(1 << ((8 * n_bytes) - 1))
    # Construct the format string
    fmt = f"<i{n_bytes:d}"
    # Rescale and format the data buffer
    out = scale * np.frombuffer(buf, fmt).astype(dtype)
    return out


def info_soundfile(fp):
    info = {}
    info["duration"] = sf.info(fp).duration
    info["samples"] = int(sf.info(fp).duration * sf.info(fp).samplerate)
    info["channels"] = sf.info(fp).channels
    info["sampling_rate"] = sf.info(fp).samplerate
    return info


def info_audioread(fp):
    info = {}
    with audioread.audio_open(fp) as f:
        info["duration"] = f.duration
    with audioread.audio_open(fp) as f:
        info["samples"] = int(f.duration * f.samplerate)
    with audioread.audio_open(fp) as f:
        info["channels"] = f.channels
    with audioread.audio_open(fp) as f:
        info["sampling_rate"] = f.samplerate
    return info


def info_ar_mad(fp):
    info = {}
    with audioread.maddec.MadAudioFile(fp) as f:
        info["duration"] = f.duration
    with audioread.maddec.MadAudioFile(fp) as f:
        info["samples"] = int(f.duration * f.samplerate)
    with audioread.maddec.MadAudioFile(fp) as f:
        info["channels"] = f.channels
    with audioread.maddec.MadAudioFile(fp) as f:
        info["sampling_rate"] = f.samplerate
    return info


def info_ar_ffmpeg(fp):
    info = {}
    with audioread.ffdec.FFmpegAudioFile(fp) as f:
        info["duration"] = f.duration
    with audioread.ffdec.FFmpegAudioFile(fp) as f:
        info["samples"] = int(f.duration * f.samplerate)
    with audioread.ffdec.FFmpegAudioFile(fp) as f:
        info["channels"] = f.channels
    with audioread.ffdec.FFmpegAudioFile(fp) as f:
        info["sampling_rate"] = f.samplerate
    return info


def info_sox(fp):
    info = {}
    info["duration"] = sox.file_info.duration(fp)
    info["samples"] = sox.file_info.num_samples(fp)
    info["channels"] = sox.file_info.channels(fp)
    info["sampling_rate"] = int(sox.file_info.sample_rate(fp))
    return info


def info_audiofile(fp):
    info = {}
    info["duration"] = af.duration(fp)
    info["samples"] = af.samples(fp)
    info["channels"] = af.channels
    info["sampling_rate"] = af.sampling_rate
    return info


def info_audiofile_sloppy(fp):
    info = {}
    info["duration"] = af.duration(fp, sloppy=True)
    info["samples"] = af.samples(fp)
    info["channels"] = af.channels
    info["sampling_rate"] = af.sampling_rate
    return info


def info_pedalboard(fp):
    info = {}
    with pedalboard.io.AudioFile(fp) as af:
        info["duration"] = af.duration
    with pedalboard.io.AudioFile(fp) as af:
        info["samples"] = af.frames
    with pedalboard.io.AudioFile(fp) as af:
        info["channels"] = af.num_channels
    with pedalboard.io.AudioFile(fp) as af:
        info["sampling_rate"] = af.samplerate
    return info
