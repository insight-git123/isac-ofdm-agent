"""CFAR 检测器单元测试。"""
import sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.simulation.cfar import ca_cfar_2d


def test_cfar_detects_strong_target():
    """人工构造单目标 RDM，CFAR 应能检测到。"""
    rdm = np.random.rand(50, 50) * 0.1     # 背景噪声
    rdm[25, 25] = 10.0                      # 强目标
    detected = ca_cfar_2d(rdm, guard_cells=2, train_cells=4, pfa=1e-2)
    assert detected[25, 25] is np.True_


def test_cfar_no_false_alarm_on_noise():
    """纯噪声场景 CFAR 不应产生大量虚警。"""
    np.random.seed(0)
    rdm = np.random.rand(100, 100) * 0.1
    detected = ca_cfar_2d(rdm, guard_cells=2, train_cells=4, pfa=1e-4)
    # 允许少量虚警，但不应超过 5%
    assert np.sum(detected) < 100 * 100 * 0.05