#!/usr/bin/env bash
set -euo pipefail

echo "========================================="
echo "   ISAC-OFDM Agent 全流程一键复现脚本"
echo "========================================="

# 激活虚拟环境（如果是 Windows Git Bash）
if [ -d ".venv/Scripts" ]; then
    source .venv/Scripts/activate
elif [ -d ".venv/bin" ]; then
    source .venv/bin/activate
fi

echo -e "\n[1/5] 运行 Task1: 参数提取与验证..."
python tasks/task1_run.py

echo -e "\n[2/5] 运行 Task2: OFDM 波形生成..."
python tasks/task2_run.py

echo -e "\n[3/5] 运行 Task4: Numerology 参数扫描..."
python tasks/task4_run.py

echo -e "\n[4/5] 运行 Task3: ISAC 雷达感知仿真..."
python tasks/task3_run.py

echo -e "\n[5/5] 运行 Task5: 自动报告生成..."
python tasks/task5_run.py

echo -e "\n========================================="
echo "   ✅ 所有任务执行完毕！"
echo "   报告路径: outputs/task5/experiment_report.md"
echo "========================================="