
---

### 文件 3：`LIMITATIONS.md`（完整替换）

```markdown
# 已知局限 (Known Limitations)

本文档诚实列出项目当前的**技术边界**，避免过度宣称"标准一致性"。

> **修复摘要**：
> - ✅ **P0**：输入路径动态解析 + 诚实定位
> - ✅ **P1**：TDL-A/B/C/D/E 抽头表补全（23/23/24/13/14 抽头）；CFAR 重写为功率域 + Pfa 校准
> - ✅ **P2**：QPSK/16QAM/64QAM/256QAM 调制；NR 资源网格；报告全动态生成；95% 置信区间
> - ✅ **P3**：MIMO ULA/UPA + 3D-FFT；(2,1,3) 卷积码 + Viterbi；SS/PBCH block；CP-OFDM 时域全链路

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
- **Task3 核心链路已统一**：`RadarSimulator.generate_echo()` 调用 `tdl_frequency_response()`。
- **仍存在的简化**：
  - Rician K-factor 记录但未实现独立 LOS 相位控制
  - 多普勒谱用单频近似，未做 Jakes 建模
  - 多径时延分辨率受 FFT 采样限制

## 3. OFDM 信号模型

- **已实现**（P2.4 + P3.4）：
  - NR 资源网格：DC 置零、保护带、DMRS、PRS
  - QPSK/16QAM/64QAM/256QAM 调制
  - **完整 CP-OFDM 收发链**：IFFT → 插 CP → 时域 FIR 信道 → 去 CP → FFT
  - 时域/频域等效性定量验证（CP ≥ 信道时延 → ISI < 1e-30）
  - 过采样链路（可选占用部分子载波）
- **仍存在的简化**：
  - 未实现 SSB 与 PDSCH 的时频复用（P3.3 实现了独立 SSB）
  - 未实现预编码、层映射、码字扰码
  - **已实现**：(2,1,3) 卷积码 + Viterbi（P3.2）；**未实现**：NR 标准 LDPC/Polar

## 4. CFAR 检测

- **已重写为功率域**：明确接收 `|rdm|^2`，使用标准 CA-CFAR 阈值公式。
- **已做 Pfa 校准**：`test_cfar_pfa_calibration` 验证纯噪声下实测 Pfa 接近设定值。
- **边界已处理**：用镜像 padding 避免边界漏检。
- **仍缺少**：OS-CFAR / GO-CFAR 对比实现。

## 5. 鬼影抑制

- **规则较强**：依赖"鬼影距离更远 + 幅度更低 + 偏移在特定范围"等先验假设。
- **测试数据可能有循环论证**：测试用例是按实现规则构造的。
- **未报告误抑制率**：没有统计真实目标被误判为鬼影的比例。

## 6. 报告生成

- **已完全动态化**（P2.2）：所有结论从 JSON 结果生成，无硬编码。
- **仍缺少**：commit hash / 依赖版本号未嵌入报告。

## 7. 测试覆盖

- **86 个单元测试**（P3 完成时）：
  - test_cfar (5), test_ghost (2), test_modulation (7)
  - test_nr_grid (11), test_pulse_compression (3), test_report (3)
  - test_task1 (3), test_tdl_model (12), test_mimo (7)
  - test_coding (8), test_ssb (14), test_cp_ofdm (11)
- **没有真实 PDF 端到端测试**（CI 用脱敏样例）。

## 8. 项目定位

| 层级 | 当前状态 | 说明 |
|---|---|---|
| 教学演示 | ✅ 具备 | 可运行，结构清晰 |
| 研究原型 | ✅ 具备 | 有标准信道、MIMO、编码、统计评估 |
| 3GPP 一致性工具 | ❌ 不具备 | 需完整参数、模型和验证 |

**本项目定位为"教学/研究型 OFDM-ISAC 仿真原型"，不声称 3GPP 标准一致性。**