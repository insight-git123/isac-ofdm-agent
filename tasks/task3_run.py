"""Task3 端到端：ISAC 感知仿真 -> 距离-多普勒图"""
import sys
from pathlib import Path
import yaml
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.simulation.radar_processing import RadarSimulator

def main():
    params_path = ROOT / "outputs" / "task1" / "params.yaml"
    if not params_path.exists():
        print("错误: 找不到 params.yaml，请先运行 Task1")
        return 1

    with open(params_path, "r", encoding="utf-8") as f:
        params = yaml.safe_load(f)

    # 选用 mu=0 (SCS=15kHz) 作为仿真基础
    target_num = next((n for n in params["numerology"] if n["mu"] == 0), None)
    scs_khz = target_num["scs_khz"]

    # 设定雷达参数
    fft_size = 1024
    num_symbols = 64
    sim = RadarSimulator(scs_khz=scs_khz, fft_size=fft_size, num_symbols=num_symbols, fc_ghz=3.5)

    print(f"[Task3] ISAC 感知仿真启动")
    print(f"  参数: SCS={scs_khz}kHz, FFT={fft_size}, Symbols={num_symbols}")
    print(f"  带宽: {sim.bandwidth/1e6:.2f} MHz, 距离分辨率: {sim.c/(2*sim.bandwidth):.2f} m")

    # 设定目标：距离 150m, 速度 30m/s (约 108km/h)
    true_range, true_velocity = 150.0, 30.0
    print(f"  目标真值: 距离={true_range}m, 速度={true_velocity}m/s")

    # 生成回波并计算 RDM
    Y = sim.generate_echo(target_range=true_range, target_velocity=true_velocity, snr_db=20)
    rdm, range_axis, velocity_axis = sim.compute_rdm(Y)

    # 归一化并转 dB
    rdm_db = 20 * np.log10(np.abs(rdm) / np.max(np.abs(rdm)) + 1e-12)

    # 绘制 RDM
    out_dir = ROOT / "outputs" / "task3"
    out_dir.mkdir(parents=True, exist_ok=True)
    plot_path = out_dir / "range_doppler_map.png"

    plt.figure(figsize=(10, 6))
    plt.imshow(rdm_db, aspect='auto', cmap='jet',
               extent=[velocity_axis[0], velocity_axis[-1], range_axis[0], range_axis[-1]],
               origin='lower', vmin=-40, vmax=0)
    plt.colorbar(label='Normalized Magnitude (dB)')
    plt.title(f"ISAC Range-Doppler Map (Target: {true_range}m, {true_velocity}m/s)")
    plt.xlabel("Velocity (m/s)")
    plt.ylabel("Range (m)")
    plt.axvline(true_velocity, color='white', linestyle='--', alpha=0.6, label='True Velocity')
    plt.axhline(true_range, color='white', linestyle='--', alpha=0.6, label='True Range')
    plt.legend(loc='upper right')
    plt.tight_layout()
    plt.savefig(plot_path, dpi=150)
    plt.close()

    print(f"[output] 距离-多普勒图已保存至: {plot_path}")
    print("[Task3] 完成！")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())