#!/bin/bash

# Libraries
sudo apt install -y sox ffmpeg libsox-fmt-mp3
sudo apt install -y libavresample-dev libswresample-dev libavutil-dev
sudo apt install -y libavcodec-dev libavformat-dev libsamplerate0-dev
sudo apt install -y libcairo2-dev libmad0-dev libgirepository1.0-dev

# Create and activate Python virtual environment
if command -v deactivate &> /dev/null
then
    deactivate
fi
ENV_DIR="${HOME}/.envs/audiofile-benchmark"
rm -rf ${ENV_DIR}
virtualenv --python=python3.10 ${ENV_DIR}
source ${ENV_DIR}/bin/activate
pip install --upgrade pip

# Enforce rebuilding of wheels
pip cache purge

pip install -r requirements.txt.lock
