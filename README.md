# ISAC-OFDM Agent

基于 3GPP Rel-18 标准的 ISAC（通信感知一体化）OFDM 感知仿真原型。

## 项目简介

本项目从 **3GPP TS 38.211 v18.4.0 真实 PDF** 出发，自动提取 numerology 参数，
并完成从 OFDM 波形生成 → 严格时域脉冲压缩 → 3GPP TDL 标准多径信道 → CFAR 检测 →
多径鬼影抑制 → 自动实验报告的**完整 ISAC 感知链路**。

## 核心特性

| 模块 | 功能 | 关键技术 |
|---|---|---|
| **Task1** | 3GPP 参数提取 | pdfplumber + 容错正则，解析 9193 行真实 PDF |
| **Task2** | OFDM 波形生成 | IFFT + CP 插入，支持 `--mu` 动态参数 |
| **Task3** | ISAC 感知 | **严格时域脉冲压缩** + **3GPP TR 38.901 TDL-A** + Swerling-I + CFAR + NMS + 鬼影抑制 |
| **Task4** | 性能扫描 | 蒙特卡洛 (10 次) + 自适应容差 + 分辨率公式验证 |
| **Task5** | 自动报告 | Markdown 一键生成 |

## 目录结构
