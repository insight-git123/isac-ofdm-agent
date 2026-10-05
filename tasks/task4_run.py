"""Task4: ISAC 感知性能扫描 - 蒙特卡洛 + 95% 置信区间。

P2.3 更新:
- MC 次数从 10 提升到 50 (可通过 --mc-trials 配置)
- 计算 95% 置信区间 (正态近似)
- 输出 JSON 增加 ci95_hits 字段
"""
import sys
import json
import yaml
import argparse
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.simulation.radar_processing import RadarSimulator
from src.simulation.cfar import ca_cfar_2d


def cluster_detections(rdm_mag, detected, range_axis, velocity_axis,
                       r_gate=3, v_gate=3):
    """NMS 聚类，返回 (ranges, velocities, mags)。"""
    rows, cols = np.where(detected)
    if len(rows) == 0:
        return [], [], []
    points = sorted(zip(rows, cols), key=lambda p: -rdm_mag[p[0], p[1]])
    clustered = []
    for (r, c) in points:
        if not any(abs(r - cr) <= r_gate and abs(c - cc) <= v_gate
                   for cr, cc in clustered):
            clustered.append((r, c))
    det_ranges = [range_axis[r] for r, _ in clustered]
    det_velocities = [velocity_axis[c] for _, c in clustered]
    det_mags = [rdm_mag[r, c] for r, c in clustered]
    return det_ranges, det_velocities, det_mags


def ci95_from_list(values):
    """95% 置信区间半宽 (正态近似): 1.96 * std / sqrt(n)。"""
    n = len(values)
    if n < 2:
        return 0.0
    return 1.96 * np.std(values, ddof=1) / np.sqrt(n)


def run_single_mu(mu, scs_khz, cp_duration_us, targets,
                  snr_db=20, use_swerling=True, use_multipath=True,
                  tdl_model="TDL-A", rms_delay_ns=5.0,
                  n_trials=50, base_seed=42):
    """对单个 mu 运行 N 次蒙特卡洛，返回统计量。"""
    if scs_khz <= 60:
        num_sym = 64
    elif scs_khz <= 240:
        num_sym = 256
    elif scs_khz <= 480:
        num_sym = 512
    else:
        num_sym = 2048

    hits_list, ghosts_list = [], []
    range_res_final = None
    bandwidth_final = None
    velocity_res_final = None

    for trial in range(n_trials):
        np.random.seed(base_seed + trial)

        sim = RadarSimulator(scs_khz=scs_khz, fft_size=1024,
                             num_symbols=num_sym, fc_ghz=3.5)
        bandwidth_final = sim.bandwidth
        range_res_final = sim.c / (2 * sim.bandwidth)
        cpi = num_sym * sim.symbol_duration
        velocity_res_final = sim.c / (2 * sim.fc_ghz * 1e9 * cpi)

        X, Y = sim.generate_echo(
            targets=targets, snr_db=snr_db,
            use_swerling=use_swerling,
            use_multipath=use_multipath,
            tdl_model=tdl_model,
            rms_delay_ns=rms_delay_ns,
        )
        rdm_mag, range_axis, velocity_axis = sim.compute_rdm(X, Y)

        # CFAR: 功率域 + Pfa=1e-3 + 峰值过滤
        rdm_power = np.abs(rdm_mag) ** 2
        detected_cfar = ca_cfar_2d(rdm_power, guard_cells=2,
                                   train_cells=4, pfa=1e-3)
        max_power = np.max(rdm_power)
        detected = detected_cfar & (rdm_power > max_power * 0.1)

        # NMS 自适应距离门限
        r_gate_phys = 20.0
        r_gate = max(3, int(round(r_gate_phys / range_res_final)))
        v_gate = 3
        det_ranges, det_velocities, det_mags = cluster_detections(
            rdm_mag, detected, range_axis, velocity_axis,
            r_gate=r_gate, v_gate=v_gate
        )

        R_TOL = max(5.0, 2 * range_res_final)
        V_TOL = max(20.0, 2 * velocity_res_final)
        true_hits = 0
        for tgt in targets:
            for (r, v) in zip(det_ranges, det_velocities):
                if abs(r - tgt["range"]) <= R_TOL and abs(v - tgt["velocity"]) <= V_TOL:
                    true_hits += 1
                    break

        hits_list.append(true_hits)
        ghosts_list.append(len(det_ranges) - true_hits)

    avg_hits = float(np.mean(hits_list))
    avg_ghosts = float(np.mean(ghosts_list))
    std_hits = float(np.std(hits_list, ddof=1)) if len(hits_list) > 1 else 0.0
    ci95_hits = ci95_from_list(hits_list)
    ci95_ghosts = ci95_from_list(ghosts_list)

    return {
        "mu": mu,
        "scs_khz": scs_khz,
        "cp_duration_us": cp_duration_us,
        "num_symbols": num_sym,
        "bandwidth_mhz": round(bandwidth_final / 1e6, 2),
        "range_res_m": round(range_res_final, 2),
        "velocity_res_ms": round(velocity_res_final, 2),
        "n_trials": n_trials,
        "avg_hits": round(avg_hits, 2),
        "std_hits": round(std_hits, 2),
        "ci95_hits": round(ci95_hits, 3),
        "avg_ghosts": round(avg_ghosts, 2),
        "ci95_ghosts": round(ci95_ghosts, 3),
        "detection_rate": round(avg_hits / len(targets), 3),
        "hits_list": hits_list,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mc-trials", type=int, default=50,
                        help="蒙特卡洛次数 (默认 50)")
    args = parser.parse_args()

    params_path = ROOT / "outputs" / "task1" / "params.yaml"
    with open(params_path, "r", encoding="utf-8") as f:
        params = yaml.safe_load(f)

    targets = [
        {"range": 150.0, "velocity": 30.0, "rcs": 1.0},
        {"range": 300.0, "velocity": -20.0, "rcs": 0.5},
        {"range": 450.0, "velocity": 0.0, "rcs": 0.8},
    ]

    N_TRIALS = args.mc_trials
    RMS_DELAY_NS = 5.0

    print(f"[Task4] ISAC 感知性能扫描 (TDL-A {RMS_DELAY_NS}ns RMS, Swerling-I)")
    print(f"  蒙特卡洛: {N_TRIALS} 次/μ")
    print(f"  CFAR: Pfa=1e-3, 功率域 + 峰值过滤 (-10dB)")
    print(f"  统计: 95% 置信区间 (正态近似)")
    print(f"  目标: {[(t['range'], t['velocity']) for t in targets]}\n")

    results = []
    for num in params["numerology"]:
        mu = num["mu"]
        scs_khz = num["scs_khz"]
        cp_dur = num["cp_duration_us"]
        print(f"  [mu={mu}] SCS={scs_khz}kHz, {N_TRIALS} 次 MC...")
        res = run_single_mu(mu, scs_khz, cp_dur, targets,
                            n_trials=N_TRIALS, rms_delay_ns=RMS_DELAY_NS)
        results.append(res)
        print(f"    命中: {res['avg_hits']:.2f} ± {res['ci95_hits']:.2f} (95% CI), "
              f"鬼影: {res['avg_ghosts']:.2f} ± {res['ci95_ghosts']:.2f}")

    out_dir = ROOT / "outputs" / "task4"
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / "isac_sweep_report.json"
    json_path.write_text(json.dumps(results, indent=2, ensure_ascii=False),
                          encoding="utf-8")

    # ========== 可视化 ==========
    mus = [r["mu"] for r in results]
    det_pct = [r["avg_hits"] / 3 * 100 for r in results]
    det_ci_pct = [r["ci95_hits"] / 3 * 100 for r in results]
    ghosts = [r["avg_ghosts"] for r in results]
    ghost_ci = [r["ci95_ghosts"] for r in results]
    range_res = [r["range_res_m"] for r in results]

    fig, axes = plt.subplots(1, 3, figsize=(15, 4))

    # 图 1: 检测率 + 95% CI 误差棒
    axes[0].bar(mus, det_pct, yerr=det_ci_pct, color='steelblue',
                capsize=5, error_kw={'elinewidth': 2, 'ecolor': 'darkred'})
    axes[0].set_xlabel("mu"); axes[0].set_ylabel("Detection Rate (%)")
    axes[0].set_title(f"Detection Rate ({N_TRIALS} MC, 95% CI)")
    axes[0].set_xticks(mus); axes[0].set_ylim(0, 110)
    for i, (v, e) in enumerate(zip(det_pct, det_ci_pct)):
        axes[0].text(mus[i], v + e + 3, f"{v:.0f}%", ha='center')

    # 图 2: 鬼影数 + CI
    axes[1].bar(mus, ghosts, yerr=ghost_ci, color='coral',
                capsize=5, error_kw={'elinewidth': 2, 'ecolor': 'darkred'})
    axes[1].set_xlabel("mu"); axes[1].set_ylabel("Avg Ghost Count")
    axes[1].set_title(f"Multipath Ghosts ({N_TRIALS} MC, 95% CI)")
    axes[1].set_xticks(mus)
    for i, (v, e) in enumerate(zip(ghosts, ghost_ci)):
        axes[1].text(mus[i], v + e + 0.2, f"{v:.1f}", ha='center')

    # 图 3: 距离分辨率
    axes[2].bar(mus, range_res, color='seagreen')
    axes[2].set_xlabel("mu"); axes[2].set_ylabel("Range Resolution (m)")
    axes[2].set_title("Range Resolution")
    axes[2].set_xticks(mus); axes[2].set_yscale('log')

    plt.tight_layout()
    plot_path = out_dir / "isac_sweep_summary.png"
    plt.savefig(plot_path, dpi=150)
    plt.close()

    # ========== 终端汇总表 ==========
    print("\n" + "=" * 100)
    print(f"{'mu':<4}{'SCS':<8}{'BW(MHz)':<10}{'Res(m)':<10}"
          f"{'命中 (95% CI)':<22}{'鬼影 (95% CI)':<20}{'检测率':<8}")
    print("-" * 100)
    for r in results:
        hit_str = f"{r['avg_hits']:.2f}±{r['ci95_hits']:.2f}"
        ghost_str = f"{r['avg_ghosts']:.2f}±{r['ci95_ghosts']:.2f}"
        print(f"{r['mu']:<4}{r['scs_khz']:<8}{r['bandwidth_mhz']:<10}"
              f"{r['range_res_m']:<10}{hit_str:<22}{ghost_str:<20}"
              f"{r['detection_rate']*100:.0f}%")
    print("=" * 100)

    print(f"\n[output] JSON: {json_path}")
    print(f"[output] 汇总图: {plot_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())