# audiofile benchmarks

## Installation

Make sure build dependencies are installed,
e.g. under Ubuntu:

```bash
$ sudo apt install libcairo2-dev libmad0-dev libgirepository1.0-dev sox libsox-fmt-mp3 ffmpeg mediainfo
```

Then create a virtual environment
and install the Python packages:

```bash
$ pip install -r requirements.txt.lock
```

## Usage

First generate the needed audio data:

```bash
$ bash generate_audio.sh
```

Execute the benchmarks with:

```bash
$ bash run.sh
```
