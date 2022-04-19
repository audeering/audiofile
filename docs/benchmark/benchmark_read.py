import argparse
import os
import random
import time

import matplotlib
import numpy as np

import utils
import loaders


matplotlib.use('Agg')


def get_files(dir, extension):
    audio_files = []
    dir = os.path.expanduser(dir)
    for root, _, fnames in sorted(os.walk(dir)):
        for fname in fnames:
            if fname.endswith(extension):
                path = os.path.join(root, fname)
                item = path
                audio_files.append(item)
    return audio_files


class AudioFolder(object):
    def __init__(
        self,
        root,
        download=True,
        extension='wav',
        lib="librosa",
    ):
        self.root = os.path.expanduser(root)
        self.data = []
        self.audio_files = get_files(dir=self.root, extension=extension)
        self.loader_function = getattr(loaders, lib)

    def __getitem__(self, index):
        return self.loader_function(self.audio_files[index])

    def __len__(self):
        return len(self.audio_files)


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Process some integers.')
    parser.add_argument('--ext', type=str, default="wav")
    args = parser.parse_args()

    columns = [
        'ext',
        'lib',
        'duration',
        'time',
    ]

    store = utils.DF_writer(columns)

    # libraries to be benchmarked
    libs = [
        'ar_ffmpeg',
        'ar_mad',
        'aubio',
        'audiofile',
        'librosa',
        'scipy',
        'soundfile',
    ]

    for lib in libs:
        print(f"Benchmark read {args.ext} with {lib}")
        for root, dirs, fnames in sorted(os.walk('AUDIO')):
            for audio_dir in dirs:

                # Not all libraries support all file formats
                if lib == 'scipy' and args.ext != 'wav':
                    continue
                if lib == 'ar_mad' and args.ext != 'mp3':
                    continue
                if lib == 'soundfile' and args.ext in ['mp3', 'mp4']:
                    continue

                duration = int(audio_dir)
                dataset = AudioFolder(
                    os.path.join(root, audio_dir),
                    lib='load_' + lib,
                    extension=args.ext,
                )

                start = time.time()

                for fp in dataset.audio_files:
                    audio = dataset.loader_function(fp)
                    np.max(audio)

                end = time.time()
                store.append(
                    ext=args.ext,
                    lib=lib,
                    duration=duration,
                    time=float(end - start) / len(dataset),
                )

    store.df.to_pickle(f'results/benchmark_read_{args.ext}.pickle')
