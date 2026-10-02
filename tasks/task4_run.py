"""Task4 端到端：参数扫描 + 生成报告"""
import sys
import json
import yaml
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.sweep.numerology_sweep import run_sweep, plot_results

def main():
    params_path = ROOT / "outputs" / "task1" / "params.yaml"
    if not params_path.exists():
        print("错误: 找不到 params.yaml，请先运行 Task1")
        return 1

    with open(params_path, "r", encoding="utf-8") as f:
        params = yaml.safe_load(f)

    print("[Task4] 开始 numerology 参数扫描...")
    results = run_sweep(params, fft_size=1024)

    out_dir = ROOT / "outputs" / "task4"
    out_dir.mkdir(parents=True, exist_ok=True)

    # 1. 保存 JSON 报告
    report_path = out_dir / "sweep_report.json"
    report_path.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")

    # 2. 绘制柱状图
    plot_path = out_dir / "cp_overhead.png"
    plot_results(results, plot_path)

    # 3. 终端打印
    print(f"{'μ':<4} {'SCS(kHz)':<10} {'CP(us)':<10} {'CP Samples':<12} {'Overhead':<10}")
    print("-" * 50)
    for r in results:
        print(f"{r['mu']:<4} {r['scs_khz']:<10} {r['cp_duration_us']:<10} {r['cp_samples']:<12} {r['cp_overhead']*100:.2f}%")

    print(f"\n[output] 扫描报告: {report_path}")
    print(f"[output] 开销对比图: {plot_path}")
    print("[Task4] 完成！")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())