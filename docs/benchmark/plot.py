import sys

import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt


NBFILES = 10  # must be identical to generate_audio.sh


for package in ['read', 'info']:
    dfs = []
    for ext in ["wav", "mp3", "mp4", "ogg", "flac"]:
        dfs.append(pd.read_pickle(f'results/benchmark_{package}_{ext}.pickle'))

    df = pd.concat(dfs, ignore_index=True)

    sns.set_style("whitegrid")

    df_ = df[df['ext'] == 'wav']
    df_ = df_[df_['lib'] == 'audiofile']
    number_of_files = len(df_) * NBFILES

    for exts in [['wav', 'flac', 'ogg'], ['mp3', 'mp4']]:

        y = df[df['ext'].isin(exts)]

        # Find best audioread entry
        for ext in exts:
            z = df[df['ext'] == ext]
            best_time = 1000000
            for lib in ['ar_mad', 'ar_ffmpeg', 'ar_gstreamer']:
                z_lib = z.loc[z['lib'] == lib, :]
                z_lib['lib'] = 'audioread'
                y = y[y['lib'] != lib]
                current_time = z_lib['time'].mean()
                if current_time < best_time:
                    best_lib = z_lib
                    best_time = current_time
            y = pd.concat([y, best_lib])

        common_libs = ['audiofile', 'soundfile', 'aubio', 'librosa']
        if 'wav' in exts:
            # Don't show audioread and sox as they are too slow
            lib_order = common_libs + ['scipy']
        else:
            lib_order = common_libs + ['audioread']

        fig = plt.figure()

        g = sns.catplot(
            x="time",
            y="ext",
            kind='bar',
            hue='lib',
            hue_order=lib_order,
            order=exts,
            data=y,
            height=5.6,
            aspect=1.2,
            legend=False
        )
        g.despine(left=True)
        plt.legend(loc='upper right')
        plt.xlabel('time / s per file')
        plt.ylabel('file format')
        if package == 'info':
            plt.title(f'Access metadata, average over {number_of_files} files')
        else:
            plt.title(f'Read file, average over {number_of_files} files')
        g.savefig(f'results/benchmark_{"-".join(exts)}_{package}.png')
        plt.close()
