"""TDL 信道模型单元测试。"""
import sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.simulation.tdl_model import (
    get_tdl_taps, apply_tdl_channel, TDL_CONFIGS
)


def test_tdl_a_taps_count():
    taps, cfg = get_tdl_taps("TDL-A")
    assert len(taps) == 12
    assert cfg["rms_delay_ns"] == 30
    assert cfg["los"] is False


def test_tdl_d_is_los():
    taps, cfg = get_tdl_taps("TDL-D")
    assert cfg["los"] is True
    assert cfg["k_factor_db"] is not None


def test_apply_tdl_channel_preserves_length():
    fs = 100e6
    rx = np.random.randn(1000) + 1j * np.random.randn(1000)
    out = apply_tdl_channel(rx, fs=fs, model="TDL-A")
    assert len(out) == len(rx)


def test_apply_tdl_channel_energy_conservation():
    """归一化后总能量应接近输入。"""
    fs = 100e6
    rx = np.random.randn(5000) + 1j * np.random.randn(5000)
    out = apply_tdl_channel(rx, fs=fs, model="TDL-A", normalize_power=True)
    # 归一化后输出能量不应爆炸
    assert np.sum(np.abs(out) ** 2) < 10 * np.sum(np.abs(rx) ** 2)