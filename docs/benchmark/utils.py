import os

import matplotlib
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns


matplotlib.use("Agg")
DEVNULL = open(os.devnull, "w")


class DFWriter(object):
    def __init__(self, columns):
        self.df = pd.DataFrame(columns=columns)
        self.columns = columns

    def append(self, **row_data):
        if set(self.columns) == set(row_data):
            new_df = pd.DataFrame.from_records([row_data])
            if len(self.df) == 0:
                self.df = new_df
            else:
                self.df = pd.concat([self.df, new_df], ignore_index=True)


def plot_results(df, target_lib="", audio_format="", ext="png"):
    sns.set_style("whitegrid")

    ordered_libs = df.time.groupby(df.lib).mean().sort_values().index.tolist()

    fig = plt.figure()

    g = sns.catplot(
        x="duration",
        y="time",
        kind="point",
        hue_order=ordered_libs,
        hue="lib",
        data=df,
        height=6.6,
        aspect=1,
    )

    g.savefig("benchmark_%s_%s_dur.%s" % (target_lib, audio_format, ext))

    fig = plt.figure()
    sns.barplot(x="time", y="lib", data=df, order=ordered_libs, orient="h")
    fig.savefig(
        f"benchmark_{target_lib}_{audio_format}_bar.{ext}",
        bbox_inches="tight",
    )
