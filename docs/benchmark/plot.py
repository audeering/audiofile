import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns


NBFILES = 10  # must be identical to generate_audio.sh

MAPPINGS = {  # library name mappings
    "audiofile": "audiofile",
    "audiofile_sloppy": "audiofile (sloppy)",
    "audioread": "audioread",
    "librosa": "librosa",
    "pedalboard": "pedalboard",
    "scipy": "scipy",
    "soundfile": "soundfile",
    "sox": "sox",
}

for package in ["read", "info"]:
    dfs = []
    for ext in ["wav", "mp3", "mp4", "ogg", "flac"]:
        dfs.append(pd.read_pickle(f"results/benchmark_{package}_{ext}.pickle"))

    df = pd.concat(dfs, ignore_index=True)

    sns.set_style("whitegrid")

    df_ = df[df["ext"] == "wav"]
    df_ = df_[df_["lib"] == "audiofile"]
    number_of_files = len(df_) * NBFILES

    df["lib"] = df["lib"].map(MAPPINGS)

    if package == "read":
        extensions = [["wav", "flac", "ogg", "mp3", "mp4"]]  # single graph
    else:
        extensions = [["wav", "flac", "ogg", "mp3"], ["mp4"]]

    for exts in extensions:
        y = df[df["ext"].isin(exts)]

        # Define what to show in each figure
        if package == "read":
            lib_order = [
                MAPPINGS["audiofile"],
                MAPPINGS["soundfile"],
                MAPPINGS["librosa"],
                MAPPINGS["pedalboard"],
                MAPPINGS["audioread"],
                MAPPINGS["scipy"],
            ]
            height = 5.8
            aspect = 1.0
        elif package == "info" and "wav" in exts:
            lib_order = [
                MAPPINGS["audiofile"],
                MAPPINGS["soundfile"],
                MAPPINGS["pedalboard"],
                MAPPINGS["audioread"],
            ]
            # Remove audioread for WAV, FLAC, OGG
            y = y[~((y["ext"] != "mp3") & (y["lib"] == "audioread"))]
            height = 4.0
            aspect = 1.6
        elif package == "info" and "mp4" in exts:
            lib_order = [
                MAPPINGS["audiofile"],
                MAPPINGS["audiofile_sloppy"],
                MAPPINGS["audioread"],
            ]
            height = 1.4
            aspect = 4.8

        fig = plt.figure()

        # Define colors for the libraries
        palette = {
            MAPPINGS["audiofile"]: "#4a74b5",
            MAPPINGS["audiofile_sloppy"]: "#6b93d7",
            MAPPINGS["soundfile"]: "#db8548",
            MAPPINGS["librosa"]: "#c34c4d",
            MAPPINGS["scipy"]: "#8174b8",
            MAPPINGS["audioread"]: "#94785e",
            MAPPINGS["sox"]: "#db8cc5",
            MAPPINGS["pedalboard"]: "#5dab64",
        }

        g = sns.catplot(
            x="time",
            y="ext",
            kind="bar",
            hue="lib",
            hue_order=lib_order,
            order=exts,
            palette=palette,
            data=y,
            height=height,
            aspect=aspect,
            legend=True,
        )
        g.despine(left=True)
        plt.xlabel("time / s per file")
        plt.ylabel("file format")
        if package == "info":
            plt.title(f"Access metadata, average over {number_of_files} files")
        else:
            plt.title(f"Read file, average over {number_of_files} files")
        g.savefig(f'results/benchmark_{"-".join(exts)}_{package}.png')
        plt.close()
