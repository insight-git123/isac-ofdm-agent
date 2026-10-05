"""CP-OFDM 全链路单元测试。"""
import sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.simulation.cp_ofdm_link import CPOFDMLink, CPOFDMLinkOversampled
from src.simulation.time_domain_channel import TimeDomainTDLChannel


def test_link_no_channel_roundtrip():
    """无信道时, 收发应完全一致。"""
    link = CPOFDMLink(n_fft=64, cp_len=8)
    X = (np.random.randn(64, 4) + 1j * np.random.randn(64, 4)) / np.sqrt(2)
    tx = link.transmit(X)
    rx = link.receive(tx, n_symbols=4)
    assert np.allclose(X, rx, atol=1e-10)


def test_link_transmit_length():
    link = CPOFDMLink(n_fft=64, cp_len=8)
    X = np.ones((64, 5), dtype=complex)
    tx = link.transmit(X)
    assert len(tx) == 5 * (64 + 8)


def test_link_cp_content():
    """CP 应为最后 cp_len 个采样的副本。"""
    link = CPOFDMLink(n_fft=64, cp_len=8)
    X = np.random.randn(64, 1) + 1j * np.random.randn(64, 1)
    tx = link.transmit(X)
    # tx[:8] 应等于 IFFT 的最后 8 个采样
    time_data = np.fft.ifft(X[:, 0]) * np.sqrt(64)
    assert np.allclose(tx[:8], time_data[-8:])


def test_channel_frequency_response_fft():
    """FIR 信道的频域响应应等于 FFT(fir)。"""
    ch = TimeDomainTDLChannel(model="TDL-A", rms_delay_ns=30,
                               fs_hz=122.88e6)
    H = ch.frequency_response(n_fft=1024)
    assert len(H) == 1024
    # H 应等于 FFT(fir)
    H_direct = np.fft.fft(ch.fir, 1024)
    assert np.allclose(H, H_direct)


def test_channel_matches_tdl_frequency_response():
    """时域 FIR 的频响应与 tdl_model 的低频段一致。

    说明: 时域 FIR 的抽头时延被量化到采样整数倍，
    高频子载波会有相位量化误差。故只对比前 100 个子载波 (低频段)。
    """
    from src.simulation.tdl_model import tdl_frequency_response
    fs = 122.88e6
    n_fft = 1024
    scs_hz = 120e3

    ch = TimeDomainTDLChannel(model="TDL-A", rms_delay_ns=30,
                               fs_hz=fs, normalize_power=True)
    H_time = ch.frequency_response(n_fft)

    H_freq = tdl_frequency_response(n_fft, scs_hz, model="TDL-A",
                                     rms_delay_ns=30,
                                     normalize_power=True).flatten()

    # 只对比前 100 个子载波 (低频段，量化误差小)
    n_compare = 100
    corr = np.corrcoef(np.abs(H_time[:n_compare]),
                       np.abs(H_freq[:n_compare]))[0, 1]
    assert corr > 0.9, f"低频段幅度相关系数 {corr} < 0.9"


def test_channel_apply_preserves_length():
    ch = TimeDomainTDLChannel(model="TDL-A", rms_delay_ns=30,
                               fs_hz=122.88e6)
    signal = np.random.randn(1000) + 1j * np.random.randn(1000)
    out = ch.apply(signal)
    assert len(out) == len(signal)


def test_oversampled_link_roundtrip():
    """过采样链路回环测试。"""
    link = CPOFDMLinkOversampled(n_fft=128, n_active_sc=64, cp_len=16)
    X = (np.random.randn(64, 3) + 1j * np.random.randn(64, 3)) / np.sqrt(2)
    tx = link.transmit(X)
    rx = link.receive(tx, n_symbols=3)
    assert rx.shape == (64, 3)
    assert np.allclose(X, rx, atol=1e-10)


def test_oversampled_transmit_length():
    link = CPOFDMLinkOversampled(n_fft=128, n_active_sc=64, cp_len=16)
    X = np.ones((64, 4), dtype=complex)
    tx = link.transmit(X)
    assert len(tx) == 4 * (128 + 16)


def test_cp_longer_than_channel_no_isi():
    """CP 长度 >= 信道时延 → 时域信道等效为频域乘法。"""
    fs = 122.88e6
    scs_hz = 120e3
    n_fft = 1024
    cp_samples = 72    # mu=3, 0.5864 us

    # CP 足够覆盖 30ns RMS 信道
    link = CPOFDMLink(n_fft=n_fft, cp_len=cp_samples)
    ch = TimeDomainTDLChannel(model="TDL-A", rms_delay_ns=30, fs_hz=fs)

    # 构造频域数据
    X = (np.random.randn(n_fft, 4) + 1j * np.random.randn(n_fft, 4)) / np.sqrt(2)

    # 发射 → 信道 → 接收
    tx = link.transmit(X)
    rx = ch.apply(tx)
    X_rx = link.receive(rx, n_symbols=4)

    # 理论: X_rx ≈ H · X (逐子载波)
    H_theory = ch.frequency_response(n_fft)
    X_expected = X * H_theory.reshape(-1, 1)

        # 相对误差 (忽略边界符号影响)
    err = np.mean(np.abs(X_rx[:, 1:-1] - X_expected[:, 1:-1]) ** 2) / \
          np.mean(np.abs(X_expected) ** 2)
    assert err < 0.01, f"CP 长度不足导致误差 {err}"


def test_cp_shorter_than_channel_increases_isi():
    """CP 长度不足时，误差应显著大于 CP 充足的场景。

    物理说明:
    - 信道最大时延 ≈ 36 采样
    - CP=72: 完全覆盖, 无 ISI
    - CP=4: 覆盖不足, ~32/1024 采样被前符号污染
    - 预期: CP 短时误差比 CP 长时高 10 倍以上
    """
    from src.simulation.modulation import modulate
    fs = 122.88e6
    n_fft = 1024

    ch = TimeDomainTDLChannel(model="TDL-A", rms_delay_ns=30, fs_hz=fs)
    H_theory = ch.frequency_response(n_fft)

    # 固定随机数据 (保证公平对比)
    rng = np.random.default_rng(42)
    qpsk_flat = modulate(n_fft * 4, "qpsk", rng=rng)
    X = qpsk_flat.reshape(n_fft, 4)
    X_expected = X * H_theory.reshape(-1, 1)

    def measure_error(cp_samples):
        link = CPOFDMLink(n_fft=n_fft, cp_len=cp_samples)
        tx = link.transmit(X)
        rx = ch.apply(tx)
        X_rx = link.receive(rx, n_symbols=4)
        return float(np.mean(np.abs(X_rx[:, 1:3] - X_expected[:, 1:3]) ** 2) /
                     np.mean(np.abs(X_expected) ** 2))

    err_long = measure_error(72)   # CP 充足
    err_short = measure_error(4)   # CP 过短

    print(f"\n  CP=72 (充足): err = {err_long:.4e}")
    print(f"  CP=4 (过短): err = {err_short:.4e}")
    print(f"  误差比 = {err_short / err_long:.1f}×")

    assert err_short > 10 * err_long, \
        f"CP 缩短后误差未显著增大: long={err_long:.4e}, short={err_short:.4e}"


def test_fir_maximum_delay():
    """FIR 滤波器最大时延应与 TDL-A 标准一致。"""
    ch = TimeDomainTDLChannel(model="TDL-A", rms_delay_ns=30, fs_hz=122.88e6)
    # TDL-A 最大归一化时延 9.6586 * 30 ns = 289.76 ns
    expected_samples = int(round(289.76e-9 * 122.88e6))  # ≈ 36
    assert ch.maximum_delay_samples() == expected_samples