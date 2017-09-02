A simple tool for making time-lapse videos, for use with a Raspberry Pi

# Usage

Install `fswebcam` using your package manager.

Clone and, in a Python-3.5+ virtualenv:

    pip install -e .

Copy `config.yml.dist` to `config.yml` and edit to your liking.  You will need
to specify some parameters for fswebcam, as well as some AWS credentials for
upload.

Run `time-lapse-pi capture` to start capture.
