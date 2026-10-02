#!/usr/bin/env bash
set -euo pipefail

echo "=== ISAC-OFDM Agent · Task1 复现 ==="
python -m pip install -r requirements.txt

echo "--- 运行任务1 ---"
python tasks/task1_run.py

echo "--- 运行评测条目1-3 ---"
python -m pytest tests/test_task1.py -v

echo "--- 产物 ---"
ls -la outputs/task1/