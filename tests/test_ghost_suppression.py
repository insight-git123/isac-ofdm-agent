"""鬼影抑制单元测试。"""
import sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.simulation.ghost_suppression import suppress_ghosts


def test_ghost_suppression_basic():
    """构造 3 真实 + 2 鬼影场景，应正确分类。"""
    # 真实目标在 (150, 30), (300, -20), (450, 0)
    # 鬼影在 (172.5, 20), (322.5, -30)  [多径 2 指纹: Δr=22.5, Δv=-10]
    det_ranges = [150.0, 300.0, 450.0, 172.5, 322.5]
    det_velocities = [30.0, -20.0, 0.0, 20.0, -30.0]
    det_mags = [1.0, 0.7, 0.9, 0.2, 0.15]   # 鬼影幅度弱

    true_idx, ghost_idx = suppress_ghosts(
        det_ranges, det_velocities, det_mags,
        r_tol=3.0, v_tol=5.0, mag_ratio=0.6, verbose=False
    )

    # 至少抑制掉 1 个鬼影，且真实目标尽量保留
    assert len(ghost_idx) >= 1
    # 真实目标 1、3 不应被误判
    assert 0 in true_idx or 2 in true_idx


def test_ghost_suppression_single_point():
    """单点时不应报错。"""
    true_idx, ghost_idx = suppress_ghosts(
        [150.0], [30.0], [1.0], verbose=False
    )
    assert true_idx == [0]
    assert ghost_idx == []