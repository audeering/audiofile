import contextlib
import os
import os.path
import time
import argparse
import utils
import loaders


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
        'audiofile_sloppy',
        'soundfile',
        'sox',
    ]

    for lib in libs:
        print(f"Benchmark metadata {args.ext} with {lib}")
        for root, dirs, fnames in sorted(os.walk('AUDIO')):
            for audio_dir in dirs:
                # MP4 and MP3 is not supported by all libraries
                if lib in ['soundfile', 'sox'] and args.ext == 'mp4':
                    continue
                if lib in ['soundfile'] and args.ext == 'mp3':
                    continue
                if lib == 'ar_mad' and args.ext != 'mp3':
                    continue
                duration = int(audio_dir)
                dataset = AudioFolder(
                    os.path.join(root, audio_dir),
                    lib='info_' + lib,
                    extension=args.ext,
                )

                start = time.time()

                # with contextlib.suppress(UserWarning):
                for fp in dataset.audio_files:
                    info = dataset.loader_function(fp)
                    info['duration']

                end = time.time()
                store.append(
                    ext=args.ext,
                    lib=lib,
                    duration=duration,
                    time=float(end - start) / len(dataset),
                )

    store.df.to_pickle(f'results/benchmark_info_{args.ext}.pickle')
