import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt


NBFILES = 10  # must be identical to generate_audio.sh

MAPPINGS = {  # library name mappings
    'audiofile': 'audiofile',
    'audiofile_sloppy': 'audiofile (sloppy)',
    'ar_ffmpeg': 'audioread (ffmpeg)',
    'ar_mad': 'audioread (mad)',
    'librosa': 'librosa',
    'pedalboard': 'pedalboard',
    'scipy': 'scipy',
    'soundfile': 'soundfile',
    'sox': 'sox',
}

for package in ['read', 'info']:
    dfs = []
    for ext in ["wav", "mp3", "mp4", "ogg", "flac"]:
        dfs.append(pd.read_pickle(f'results/benchmark_{package}_{ext}.pickle'))

    df = pd.concat(dfs, ignore_index=True)

    sns.set_style("whitegrid")

    df_ = df[df['ext'] == 'wav']
    df_ = df_[df_['lib'] == 'audiofile']
    number_of_files = len(df_) * NBFILES

    df['lib'] = df['lib'].map(MAPPINGS)

    for exts in [['wav', 'flac', 'ogg'], ['mp3', 'mp4']]:

        y = df[df['ext'].isin(exts)]

        # Define what to show in each figure
        if 'wav' in exts and package == 'read':
            lib_order = [
                MAPPINGS['audiofile'],
                MAPPINGS['soundfile'],
                MAPPINGS['librosa'],
                MAPPINGS['ar_ffmpeg'],
                MAPPINGS['pedalboard'],
                MAPPINGS['scipy'],
            ]
            height = 5.6
            aspect = 1.2
        elif 'wav' in exts and package == 'info':
            lib_order = [
                MAPPINGS['audiofile'],
                MAPPINGS['soundfile'],
                MAPPINGS['pedalboard'],
            ]
            height = 3.36
            aspect = 2.0
        elif 'mp3' in exts and package == 'read':
            lib_order = [
                MAPPINGS['audiofile'],
                MAPPINGS['librosa'],
                MAPPINGS['ar_ffmpeg'],
                MAPPINGS['ar_mad'],
                MAPPINGS['pedalboard'],
            ]
            height = 3.36
            aspect = 2.0
        elif 'mp3' in exts and package == 'info':
            lib_order = [
                MAPPINGS['audiofile'],
                MAPPINGS['audiofile_sloppy'],
                MAPPINGS['ar_ffmpeg'],
                MAPPINGS['ar_mad'],
                MAPPINGS['pedalboard'],
                MAPPINGS['sox'],
            ]
            height = 3.7
            aspect = 1.82

        fig = plt.figure()

        # Define colors for the libraries
        palette = {
            MAPPINGS['audiofile']: '#4a74b5',
            MAPPINGS['audiofile_sloppy']: '#6b93d7',
            MAPPINGS['soundfile']: '#db8548',
            MAPPINGS['librosa']: '#c34c4d',
            MAPPINGS['scipy']: '#8174b8',
            MAPPINGS['ar_mad']: '#94785e',
            MAPPINGS['ar_ffmpeg']: '#94785e',
            MAPPINGS['sox']: '#db8cc5',
            MAPPINGS['pedalboard']: '#5dab64',
        }

        g = sns.catplot(
            x="time",
            y="ext",
            kind='bar',
            hue='lib',
            hue_order=lib_order,
            order=exts,
            palette=palette,
            data=y,
            height=height,
            aspect=aspect,
            legend=True,
        )
        g.despine(left=True)
        plt.xlabel('time / s per file')
        plt.ylabel('file format')
        if package == 'info':
            plt.title(f'Access metadata, average over {number_of_files} files')
        else:
            plt.title(f'Read file, average over {number_of_files} files')
        g.savefig(f'results/benchmark_{"-".join(exts)}_{package}.png')
        plt.close()
