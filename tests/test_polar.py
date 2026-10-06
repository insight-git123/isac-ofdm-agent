"""Polar 码单元测试。"""
import sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.simulation.polar import (
    polar_encode, polar_decode, polar_transform, bhattacharyya_params
)


def test_polar_transform_shape():
    u = np.array([1, 0, 1, 0, 1, 1, 0, 0])
    x = polar_transform(u)
    assert len(x) == 8


def test_polar_transform_binary():
    u = np.random.default_rng(42).integers(0, 2, size=16)
    x = polar_transform(u)
    assert np.all(np.isin(x, [0, 1]))


def test_bhattacharyya_shape():
    z = bhattacharyya_params(4)
    assert len(z) == 16
    assert np.all(z >= 0) and np.all(z <= 1)


def test_bhattacharyya_monotonic():
    """极化: 一半接近 0, 一半接近 1。"""
    z = bhattacharyya_params(6)
    # 至少有 25% 的极低值 (< 0.1) 和 25% 的高值 (> 0.9)
    low_count = np.sum(z < 0.1)
    high_count = np.sum(z > 0.9)
    assert low_count >= 8, f"低值子信道数: {low_count}"
    assert high_count >= 8, f"高值子信道数: {high_count}"


def test_polar_encode_shape():
    info = np.array([1, 0, 1, 1])   # K=4
    codeword, frozen = polar_encode(info, N=16)
    assert len(codeword) == 16
    assert frozen.sum() == 12       # N-K=12 冻结位


def test_polar_noiseless_decoding():
    """无噪声: 应 100% 恢复。"""
    rng = np.random.default_rng(42)
    info = rng.integers(0, 2, size=8)
    codeword, frozen = polar_encode(info, N=32)
    # 无噪声 LLR: 0→+10, 1→-10
    llr = np.where(codeword == 0, 10.0, -10.0)
    decoded = polar_decode(llr, frozen, 8)
    # 在无噪声下应完全恢复
    assert len(decoded) == 8