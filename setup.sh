#!/bin/bash
# Cloud-environment setup script for the Claude Code scheduled task.
# Paste into the task's Cloud environment > Setup script.
# Python 3 + pip are pre-installed and the engine code comes from this cloned
# repo, so this only installs the data deps. The engine + TA are stdlib-only.
pip install --break-system-packages --quiet yfinance pyxirr
python3 -c "import yfinance as y; print('yfinance ok:', y.Ticker('SPY').history(period='5d').shape)" || echo "setup: yfinance smoke test failed" >&2
echo "deps installed — run: python3 run.py digest"
