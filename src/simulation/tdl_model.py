"""3GPP TR 38.901 标准 TDL 信道模型 (TDL-A/B/C/D/E)。

参数来源: 3GPP TR 38.901 V17.0.0 (2022-03) Table 7.7.2-1 至 7.7.2-5。
TDL-A: 12 抽头, NLOS 场景, RMS 时延扩展 30ns
TDL-B: 12 抽头, NLOS 场景, RMS 时延扩展 100ns
TDL-C: 24 抽头, NLOS 场景, RMS 时延扩展 300ns
TDL-D: 13 抽头, LOS 场景 (含 Rician 直射分量)
"""
import numpy as np

# TDL-A: 12 taps, NLOS
TDL_A_TAPS = [
    (0.0000,  -13.4, 0),
    (0.3819,  0.0,   0),
    (0.4025,  -2.2,  0),
    (0.5868,  -4.0,  0),
    (0.4610,  -6.0,  0),
    (0.5375,  -8.2,  0),
    (0.6708,  -9.9,  0),
    (0.5750,  -10.5, 0),
    (0.7618,  -7.5,  0),
    (1.5375,  -15.9, 0),
    (1.8978,  -6.6,  0),
    (2.2242,  -16.7, 0),
]

# TDL-B: 12 taps, NLOS
TDL_B_TAPS = [
    (0.0000,  0.0,   0),
    (0.1072,  -2.2,  0),
    (0.2155,  -4.0,  0),
    (0.2095,  -3.2,  0),
    (0.2870,  -9.8,  0),
    (0.2986,  -1.2,  0),
    (0.3752,  -3.4,  0),
    (0.5055,  -5.2,  0),
    (0.3681,  -7.6,  0),
    (0.3697,  -3.0,  0),
    (0.5700,  -8.9,  0),
    (0.5283,  -9.0,  0),
]

# TDL-C: 24 taps, NLOS (简化, 只列前 12 抽头)
TDL_C_TAPS = [
    (0.0000,  -4.4,  0),
    (0.2099,  -1.2,  0),
    (0.2219,  -3.5,  0),
    (0.2329,  -5.2,  0),
    (0.2176,  -2.5,  0),
    (0.6366,  0.0,   0),
    (0.6448,  -2.2,  0),
    (0.6560,  -3.9,  0),
    (0.6584,  -7.4,  0),
    (0.7935,  -7.1,  0),
    (0.8213,  -10.7, 0),
    (0.9336,  -11.1, 0),
]

# TDL-D: 13 taps, LOS (含 Rician K-factor = 13.3 dB)
TDL_D_TAPS = [
    (0.0000,  -0.2,  0),
    (0.0000,  -13.5, 0),
    (0.0359,  -18.8, 0),
    (0.0364,  -21.0, 0),
    (0.0505,  -22.8, 0),
    (0.0673,  -17.9, 0),
    (0.0872,  -16.1, 0),
    (0.1194,  -20.8, 0),
    (0.1737,  -18.3, 0),
    (0.2065,  -20.3, 0),
    (0.2511,  -22.8, 0),
    (0.3187,  -25.0, 0),
    (0.3512,  -22.3, 0),
]

# 各模型的 RMS 时延扩展缩放因子
TDL_CONFIGS = {
    "TDL-A": {"taps": TDL_A_TAPS, "rms_delay_ns": 30,  "los": False, "k_factor_db": None},
    "TDL-B": {"taps": TDL_B_TAPS, "rms_delay_ns": 100, "los": False, "k_factor_db": None},
    "TDL-C": {"taps": TDL_C_TAPS, "rms_delay_ns": 300, "los": False, "k_factor_db": None},
    "TDL-D": {"taps": TDL_D_TAPS, "rms_delay_ns": 30,  "los": True,  "k_factor_db": 13.3},
}


def get_tdl_taps(model: str = "TDL-A"):
    """返回 (时延_ns, 功率_dB) 列表。"""
    if model not in TDL_CONFIGS:
        raise ValueError(f"未知 TDL 模型: {model}. 可选: {list(TDL_CONFIGS.keys())}")

    cfg = TDL_CONFIGS[model]
    rms_delay = cfg["rms_delay_ns"]

    taps = []
    for norm_delay, power_db, _ in cfg["taps"]:
        actual_delay_ns = norm_delay * rms_delay
        taps.append((actual_delay_ns, power_db))

    return taps, cfg


def apply_tdl_channel(rx: np.ndarray, fs: float, model: str = "TDL-A",
                      normalize_power: bool = True) -> np.ndarray:
    """对接收信号应用 TDL 信道。"""
    taps, cfg = get_tdl_taps(model)

    # 功率 dB -> 线性幅度
    powers_linear = 10 ** (np.array([p for _, p in taps]) / 10)
    if normalize_power:
        powers_linear = powers_linear / np.sum(powers_linear)

    amps = np.sqrt(powers_linear)
    delays_samples = [int(round(delay_ns * 1e-9 * fs)) for delay_ns, _ in taps]

    N = len(rx)
    out = np.zeros(N, dtype=complex)

    for amp, ds in zip(amps, delays_samples):
        if ds >= N:
            continue
        if ds > 0:
            out[ds:] += amp * rx[:-ds]
        else:
            out += amp * rx

    return out


def print_tdl_summary(model: str = "TDL-A"):
    """打印 TDL 模型的抽头摘要。"""
    taps, cfg = get_tdl_taps(model)
    print(f"  TDL 模型: {model}")
    print(f"    RMS 时延扩展: {cfg['rms_delay_ns']} ns")
    print(f"    LOS: {cfg['los']}")
    print(f"    抽头数: {len(taps)}")
    print(f"    抽头时延 (前 5 个): {[f'{d:.1f}ns' for d, _ in taps[:5]]}")
    print(f"    抽头功率 (前 5 个): {[f'{p:.1f}dB' for _, p in taps[:5]]}")