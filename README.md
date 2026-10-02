# ISAC-OFDM Agent

基于 3GPP Rel-18 标准的 ISAC（通信感知一体化）OFDM 波形仿真与参数提取智能体。

## 项目简介
本项目实现了从 3GPP 标准文档中自动提取 OFDM 参数，并基于提取的参数完成通信波形生成、雷达感知仿真、参数扫描以及自动实验报告生成的完整闭环。

## 目录结构
- `src/ingestion/`: 3GPP 文档解析与索引
- `src/retrieval/`: 引用溯源
- `src/simulation/`: OFDM 波形生成 & 雷达回波模拟
- `src/sweep/`: 参数扫描与开销分析
- `src/validation/`: 数据校验
- `src/report/`: 自动报告生成
- `tasks/`: 各个任务的端到端运行脚本
- `tests/`: 单元测试
- `outputs/`: 生成的结果与图表

## 快速开始
```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 一键复现所有任务
./run_all.sh