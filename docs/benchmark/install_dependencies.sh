#!/bin/bash

# Libraries for audioread and aubio
sudo apt-get install -y libmad0-dev sox ffmpeg libaubio-dev
sudo apt-get install -y libavresample-dev libswresample-dev libavutil-dev
sudo apt-get install -y libavcodec-dev libavformat-dev libsamplerate0-dev

# Create and activate Python virtual environment
if command -v deactivate &> /dev/null
then
    deactivate
fi
ENV_DIR="${HOME}/.envs/audiofile-benchmark"
rm -rf ${ENV_DIR}
virtualenv --python=python3.8 ${ENV_DIR}
source ${ENV_DIR}/bin/activate
pip install --upgrade pip

# Enfore rebuolding of wheels
pip cache purge

# Fix numpy header include for aubio
pip install "numpy==1.21.6"
mkdir -p ${ENV_DIR}/include/
ln -sf ${ENV_DIR}lib/python3.8/site-packages/numpy/core/include/numpy ${ENV_DIR}/include/

pip install -r requirements.txt.lock
