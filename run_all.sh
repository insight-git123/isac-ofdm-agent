##!/usr/bin/env bash
set -euo pipefail

echo "========================================="
echo "   ISAC-OFDM Agent 全流程一键复现"
echo "========================================="

if [ -d ".venv/Scripts" ]; then
    source .venv/Scripts/activate
elif [ -d ".venv/bin" ]; then
    source .venv/bin/activate
fi

echo -e "\n[1/8] Task1: 3GPP 参数提取..."
python tasks/task1_run.py

echo -e "\n[2/8] Task2: OFDM 波形生成..."
python tasks/task2_run.py --mu 3

echo -e "\n[3/8] Task3: 严格时域脉冲压缩..."
python tasks/task3_time_domain.py --mu 3

echo -e "\n[4/8] Task3: 标准 TDL-A 多径信道..."
python tasks/task3_tdl.py --mu 3 --model TDL-A

echo -e "\n[5/8] Task3: RDM + CFAR + 鬼影抑制..."
python tasks/task3_run.py --mu 3 --swerling --multipath --suppress

echo -e "\n[6/8] Task4: 蒙特卡洛性能扫描..."
python tasks/task4_run.py

echo -e "\n[7/8] Task4: 深度分析..."
python tasks/task4_analysis.py

echo -e "\n[8/8] Task5: 自动生成报告..."
python tasks/task5_run.py

echo -e "\n========================================="
echo "   ✅ 全部完成！"
echo "   报告: outputs/task5/experiment_report.md"
echo "========================================="