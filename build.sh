#!/bin/bash
set -e

# Force Python 3.12
export PYENV_VERSION=3.12.0

# Upgrade pip to latest
pip install --upgrade pip

# Install with only pre-built wheels (no compilation)
pip install --no-cache-dir --only-binary :all: -r requirements.txt