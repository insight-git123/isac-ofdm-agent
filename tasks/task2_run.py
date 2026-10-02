"""Task2: 读取 Task1 参数，生成 OFDM 波形并绘图"""
import sys
from pathlib import Path
import yaml
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.simulation.ofdm_generator import OFDMGenerator

def main():
    # 1. 读取 Task1 生成的参数
    params_path = ROOT / "outputs" / "task1" / "params.yaml"
    if not params_path.exists():
        print("错误: 找不到 params.yaml，请先运行 Task1")
        return 1

    with open(params_path, "r", encoding="utf-8") as f:
        params = yaml.safe_load(f)

    numerology = params["numerology"]
    print(f"[Task2] 读取到 {len(numerology)} 组 numerology 参数")

    # 2. 选取 mu=0 (15kHz, 正常CP) 进行仿真
    target = next((n for n in numerology if n["mu"] == 0), None)
    if not target:
        print("错误: 未找到 mu=0 的参数")
        return 1

    print(f"  使用参数: SCS={target['scs_khz']}kHz, CP长度={target['cp_duration_us']}us")
    
    # 3. 生成波形
    generator = OFDMGenerator(
        scs_khz=target["scs_khz"],
        cp_duration_us=target["cp_duration_us"]
    )
    waveform = generator.generate(num_symbols=2)
    
    # 4. 绘图
    out_dir = ROOT / "outputs" / "task2"
    out_dir.mkdir(parents=True, exist_ok=True)
    
    plt.figure(figsize=(12, 4))
    plt.plot(np.real(waveform), label="Real Part", alpha=0.8)
    plt.plot(np.imag(waveform), label="Imag Part", alpha=0.6)
    plt.title(f"OFDM Waveform (mu=0, SCS=15kHz, CP={target['cp_duration_us']}us)")
    plt.xlabel("Sample Index")
    plt.ylabel("Amplitude")
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    
    plot_path = out_dir / "ofdm_waveform.png"
    plt.savefig(plot_path, dpi=150)
    plt.close()
    
    print(f"[output] 波形图已保存至: {plot_path}")
    print(f"[Task2] 成功！总采样点数: {len(waveform)}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())