#!/usr/bin/env bash
if command -v python3 &> /dev/null; then
    python3 -m venv .venv
elif command -v python &> /dev/null; then
    python -m venv .venv
else
    echo "Python not installed. Please install Python and then rerun this script."
    exit 1
fi

source .venv/bin/activate && pip install pytest pytest-cov > /dev/null && deactivate

source .venv/bin/activate && \
pip install --upgrade pip > /dev/null && \
pip install . > /dev/null && \
pip install '.[test]' > /dev/null && pip install '.[sbom]' > /dev/null && \
pytest --cov-report xml:coverage/coverage.xml --cov=src tests/ && \
deactivate

