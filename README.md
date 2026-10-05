# ISAC-OFDM Agent

基于 3GPP Rel-18 参数的教学/演示型 OFDM-ISAC 仿真原型。

> ⚠️ **项目定位**：本项目用于展示从 3GPP 参数提取到 ISAC 感知处理的完整链路，
> **不声称**严格 3GPP 标准一致性，也**不适合**直接作为论文结论依据。
> 已知局限详见 [LIMITATIONS.md](LIMITATIONS.md)。

## 项目简介

本项目从 3GPP TS 38.211 v18.4.0 提取 numerology 参数，并完成从
OFDM 波形生成 → 严格时域脉冲压缩 → 3GPP TDL-A 标准多径信道
→ CFAR 检测 → 多径鬼影抑制 → 自动实验报告的完整 ISAC 感知链路。

- **输入**：真实 PDF（需本地下载）或仓库内的脱敏样例文本
- **输出**：RDM 图、CFAR 检测点、多径鬼影识别、Markdown 实验报告

## 核心特性

| 模块 | 功能 | 关键技术 |
|---|---|---|
| **Task1** | 3GPP 参数提取 | pdfplumber + 容错正则，支持真实 PDF（9193 行）或样例文本 |
| **Task2** | OFDM 波形生成 | IFFT + CP 插入，支持 `--mu` 动态参数 |
| **Task3** | ISAC 感知 | **严格时域脉冲压缩** + **3GPP TR 38.901 TDL-A** + Swerling-I + CFAR + NMS + 鬼影抑制 |
| **Task4** | 性能扫描 | 蒙特卡洛 (10 次) + 自适应容差 + 分辨率公式验证 |
| **Task5** | 自动报告 | Markdown 一键生成 |

### 修复状态

- ✅ **P0**（可复现性）：输入路径动态解析 + 诚实定位 + `LIMITATIONS.md`
- ✅ **P1**（可信度）：统一 3GPP TDL-A 信道（23 抽头）+ 功率域 CA-CFAR（Pfa 校准）
- ⏳ **P2**（未来）：NR 资源网格、QPSK/16QAM 调制、统计置信区间
## 主要结果

### 时域脉冲压缩 (mu=3, BW=122.88 MHz)

![Pulse Compression](outputs/task3/pulse_compression_mu3.png)

### TDL-A 多径信道对比 (mu=3, 23 抽头)

![TDL Channel](outputs/task3/tdl_TDL-A_mu3.png)

### 多径鬼影抑制 (mu=3, Swerling + TDL-A)

使用标准 3GPP TR 38.901 TDL-A 信道（23 抽头，RMS 时延扩展 30ns，最大时延约 290ns）。
在 mu=3 的 1.22m 距离分辨率下，多径时延扩展约 **43.5m**（≈ 35 个距离门），
因此每个真实目标在 RDM 上呈现为 **"多径簇"** 而非单点：

- **绿色圈** = 簇中心（聚类后的候选真实目标）
- **红色叉** = 被鬼影抑制算法过滤掉的多径点

![Ghost Suppression](outputs/task3/rdm_mu3_swerling_multipath_ghostsuppress_cfar.png)

**物理含义**：TDL-A 的 23 个抽头分布在 43.5m 范围内，导致单目标在 RDM 上呈现宽簇。
这是**标准多径信道的正确行为**，不是算法缺陷——真实 ISAC 系统也需联合时域/角度域
处理来抑制这类多径。
![Ghost Suppression](outputs/task3/rdm_mu3_swerling_multipath_ghostsuppress_cfar.png)

### 分辨率公式验证

![Deep Analysis](outputs/task4/deep_analysis.png)