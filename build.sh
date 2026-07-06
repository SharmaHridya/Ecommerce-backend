#!/bin/bash
set -e

export PYENV_VERSION=3.12.0
pip install --upgrade pip
pip install --no-cache-dir --only-binary :all: -r requirements.txt

# RUN MIGRATIONS BEFORE SERVER STARTS
alembic upgrade head