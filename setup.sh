#!/bin/bash
# Cloud-environment setup for the Claude Code scheduled task.
# Installs data deps into the SAME python3 that runs the engine. Requires the
# environment's Network access = Full (or Limited with "Allow package managers"
# checked). Engine + TA are stdlib-only; only data/regime need yfinance.
set -e
python3 -m pip install --break-system-packages --quiet --upgrade pip || true
python3 -m pip install --break-system-packages --quiet yfinance pyxirr
# Verify the import in the exact interpreter the task will use.
python3 -c "import yfinance as y; print('yfinance ok:', y.Ticker('SPY').history(period='5d').shape)"
echo "setup done — run: python3 run.py digest"
