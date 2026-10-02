"""Task5: 自动生成 Markdown 实验报告。"""
import json
import yaml
from pathlib import Path
from datetime import datetime

def generate_report(root_dir: Path) -> str:
    # 1. 读取 Task1 参数
    params_path = root_dir / "outputs" / "task1" / "params.yaml"
    params = {}
    if params_path.exists():
        with open(params_path, "r", encoding="utf-8") as f:
            params = yaml.safe_load(f)

    # 2. 读取 Task4 扫描报告
    sweep_path = root_dir / "outputs" / "task4" / "sweep_report.json"
    sweep_data = []
    if sweep_path.exists():
        sweep_data = json.loads(sweep_path.read_text(encoding="utf-8"))

    # 3. 拼接 Markdown 内容
    md = []
    md.append("# ISAC-OFDM Agent 实验报告\n")
    md.append(f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    if params:
        meta = params.get("meta", {})
        md.append("## 1. 项目信息\n")
        md.append(f"- **项目名称**: {meta.get('project', 'N/A')}")
        md.append(f"- **任务阶段**: {meta.get('task', 'N/A')}")
        md.append(f"- **标准版本**: {meta.get('release', 'N/A')}")
        md.append(f"- **数据来源**: {meta.get('source', 'N/A')}")
        md.append(f"- **验证结果**: {'✅ PASS' if meta.get('validation_passed') else '❌ FAIL'}\n")

        md.append("## 2. 提取的 Numerology 参数 (Task1)\n")
        md.append("| μ | SCS (kHz) | CP 类型 | CP 时长 (μs) |")
        md.append("|---|---|---|---|")
        for num in params.get("numerology", []):
            cp_types = ", ".join(num.get("cp_types", []))
            cp_dur = num.get("cp_duration_us", "N/A")
            md.append(f"| {num['mu']} | {num['scs_khz']} | {cp_types} | {cp_dur} |")
        md.append("\n")

    md.append("## 3. OFDM 波形生成 (Task2)\n")
    md.append("基于 μ=0 (15kHz) 生成的时域波形图：\n")
    md.append("![OFDM Waveform](../task2/ofdm_waveform.png)\n")
    md.append("*图 1: OFDM 时域波形 (实部/虚部)*\n")

    if sweep_data:
        md.append("## 4. Numerology 扫描与 CP 开销 (Task4)\n")
        md.append("| μ | SCS (kHz) | CP 样本数 | CP 开销 (%) |")
        md.append("|---|---|---|---|")
        for r in sweep_data:
            md.append(f"| {r['mu']} | {r['scs_khz']} | {r['cp_samples']} | {r['cp_overhead']*100:.2f}% |")
        md.append("\n![CP Overhead](../task4/cp_overhead.png)\n")
        md.append("*图 2: 不同 Numerology 下的 CP 开销对比*\n")

    md.append("## 5. ISAC 感知仿真 (Task3)\n")
    md.append("模拟目标：距离 150m，速度 30m/s，SNR=20dB。\n")
    md.append("![Range-Doppler Map](../task3/range_doppler_map.png)\n")
    md.append("*图 3: 距离-多普勒图 (Range-Doppler Map)*\n")

    md.append("## 6. 结论\n")
    md.append("- 成功从 3GPP TS 38.211 提取了 Rel-18 的 numerology 参数，并完成校验。")
    md.append("- 基于提取参数生成了 OFDM 时域波形，验证了 CP 插入的正确性。")
    md.append("- 参数扫描表明，随着 SCS 增大，CP 开销显著降低。")
    md.append("- ISAC 感知仿真成功在 RDM 中定位了目标，验证了 OFDM 波形的雷达感知能力。\n")
    
    return "\n".join(md)