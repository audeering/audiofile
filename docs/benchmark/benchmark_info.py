import argparse
import os
import os.path
import time

import loaders
import utils


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
        extension="wav",
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
    parser = argparse.ArgumentParser(description="Process some integers.")
    parser.add_argument("--ext", type=str, default="wav")
    args = parser.parse_args()

    columns = [
        "ext",
        "lib",
        "duration",
        "time",
    ]

    store = utils.DFWriter(columns)

    # libraries to be benchmarked
    libs = [
        "ar_ffmpeg",
        "ar_mad",
        "audiofile",
        "audiofile_sloppy",
        "pedalboard",
        "soundfile",
        "sox",
    ]

    audio_walk = sorted(os.walk("AUDIO"))
    if len(audio_walk) == 0:
        raise RuntimeError(
            "No audio files were found.\n"
            "Make sure you executed 'bash generate_audio.sh'"
        )

    for lib in libs:
        # MP4 and MP3 is not supported by all libraries
        if lib in ["soundfile", "sox", "pedalboard"] and args.ext == "mp4":
            continue
        if lib == "ar_ffmpeg" and args.ext == "mp3":  # too slow
            continue
        if lib == "ar_mad" and args.ext != "mp3":
            continue

        print(f"Benchmark metadata {args.ext} with {lib}")
        for root, dirs, fnames in audio_walk:
            for audio_dir in dirs:
                duration = int(audio_dir)
                dataset = AudioFolder(
                    os.path.join(root, audio_dir),
                    lib="info_" + lib,
                    extension=args.ext,
                )

                start = time.time()

                # with contextlib.suppress(UserWarning):
                for fp in dataset.audio_files:
                    info = dataset.loader_function(fp)
                    info["duration"]

                end = time.time()

                # Store ar_ffmpeg and ar_mad as audioread
                if lib in ["ar_ffmpeg", "ar_mad"]:
                    lib_name = "audioread"
                else:
                    lib_name = lib

                store.append(
                    ext=args.ext,
                    lib=lib_name,
                    duration=duration,
                    time=float(end - start) / len(dataset),
                )

    store.df.to_pickle(f"results/benchmark_info_{args.ext}.pickle")
