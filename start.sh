#!/bin/bash

[[ -d ./.venv ]] || python -m venv .venv
source ./.venv/bin/activate &&
pip install -r requirements.txt
rm -f ./recording.wav ./speech.mp3 ./speech.mpeg
exec python3 -m autogpt --speak --gpt3only
