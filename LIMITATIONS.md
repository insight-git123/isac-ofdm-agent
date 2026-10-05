# 已知局限 (Known Limitations)

本文档诚实列出项目当前的**技术边界**，避免过度宣称"标准一致性"。
> **P1 修复摘要 (2026-10-05)**：
> - ✅ Task3/Task4 统一调用标准 TDL-A 信道（23 抽头）
> - ✅ TDL-A/B/C/D/E 抽头表补全
> - ✅ CFAR 重写为功率域 + Pfa 校准验证
> - ⏳ 仍待解决：NR 资源网格、QPSK/16QAM 调制、统计置信区间

## 1. 输入可复现性

- **不包含 3GPP 原始 PDF/ZIP**：仓库只保留 `data/raw/sample_ts38211.txt`（脱敏样例）。
  真实 PDF 需从 [3gpp.org](https://www.3gpp.org/ftp/Specs/archive/38_series/38.211/) 自行下载，
  并通过 `python tasks/task1_run.py --raw <path/to/ts38211.pdf>` 运行。
- **没有 SHA256 校验**：输入文件未做哈希记录，不同版本 PDF 可能解析结果不同。

## 2. TDL 信道模型

- **抽头表已补全**：
  - TDL-A: 23 抽头 (TR 38.901 Table 7.7.2-1)
  - TDL-B: 23 抽头
  - TDL-C: 24 抽头
  - TDL-D/E: LOS 场景，标注 Rician K-factor
- **Task3 核心链路已统一**：`RadarSimulator.generate_echo()` 调用 `tdl_frequency_response()`，不再使用自定义三径。
- **仍存在的简化**：
  - Rician K-factor 记录但未实现独立 LOS 相位控制
  - 多普勒谱用单频近似，未做 Jakes 建模
  - 多径时延分辨率受 FFT 采样限制
## 3. OFDM 信号模型

- **已实现 NR 资源网格**（P2.4）：
  - DC 子载波置零
  - 保护带（可配置 RB 数）
  - PDSCH DMRS（Config Type 1，symbol 2）
  - PRS（comb=4，symbol 5-8）
  - 资源网格可视化
- **已实现调制**：QPSK / 16QAM / 64QAM / 256QAM
- **仍存在的简化**：
  - 未实现完整 NR 帧结构（SSB、PDCCH、CORESET）
  - 未实现预编码、层映射、码字扰码
  - 未实现真实信道编码（LDPC/Polar）
  - DMRS 仅实现 Type 1，未实现 Type 2 和 additional positions
  - PRS 仅实现固定 comb=4，未实现 comb 组合表
## 4. CFAR 检测

- **已重写为功率域**：明确接收 `|rdm|^2`，使用标准 CA-CFAR 阈值公式 `alpha = N_train * (pfa^(-1/N_train) - 1)`
- **已做 Pfa 校准**：`test_cfar_pfa_calibration` 验证纯噪声下实测 Pfa 接近设定值
- **边界已处理**：用镜像 padding 避免边界漏检
- **仍缺少**：OS-CFAR / GO-CFAR 对比实现
## 5. 鬼影抑制

- **规则较强**：依赖"鬼影距离更远 + 幅度更低 + 偏移在特定范围"等先验假设。
- **测试数据可能有循环论证**：测试用例是按实现规则构造的，不能代表通用多径抑制算法。
- **未报告误抑制率**：没有统计真实目标被误判为鬼影的比例。

## 6. 报告生成

- **部分结论硬编码**：`report_generator.py` 中有"检测结果与理论预测一致"等
  静态文本，未完全从 JSON 结果动态生成。
- **无 commit hash / 依赖版本记录**：报告未自动嵌入运行环境信息。

## 7. 测试覆盖

- **14 个单元测试**，主要验证形状、长度、简单峰值。
- **没有真实 PDF 端到端测试**。
- **没有 TDL 抽头与标准表的逐项比对**。
- **没有 CFAR 实际 Pfa 校准测试**。
- **没有统计置信区间**（检测率、漏检率、虚警率）。

## 8. 项目定位

| 层级 | 当前状态 | 说明 |
|---|---|---|
| 教学演示 | ✅ 具备 | 可运行，结构清晰 |
| 研究原型 | ⚠️ 部分具备 | 需统一信道实现 + 统计评估 |
| 3GPP 一致性工具 | ❌ 不具备 | 需完整参数、模型和验证 |

**本项目定位为"教学/演示型 OFDM-ISAC 仿真原型"，不声称 3GPP 标准一致性。**