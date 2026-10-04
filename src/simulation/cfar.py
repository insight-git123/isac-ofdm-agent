"""CA-CFAR 检测器。"""
import numpy as np

def ca_cfar_2d(rdm_mag: np.ndarray, guard_cells: int = 2, train_cells: int = 4, pfa: float = 1e-4):
    """
    2D 单元平均 CFAR。
    rdm_mag: 2D 幅度矩阵 (距离 x 多普勒)
    guard_cells: 保护单元数 (每侧)
    train_cells: 训练单元数 (每侧)
    pfa: 虚警率
    返回: 检测结果布尔矩阵
    """
    rows, cols = rdm_mag.shape
    threshold_factor = train_cells * 2 * (pfa ** (-1 / (train_cells * 2)) - 1) # 简化的阈值因子
    
    detected = np.zeros_like(rdm_mag, dtype=bool)
    
    for i in range(guard_cells + train_cells, rows - guard_cells - train_cells):
        for j in range(guard_cells + train_cells, cols - guard_cells - train_cells):
            # 提取训练单元 (四周的矩形环)
            top = rdm_mag[i - train_cells - guard_cells : i - guard_cells, j - train_cells - guard_cells : j + train_cells + guard_cells + 1]
            bottom = rdm_mag[i + guard_cells + 1 : i + guard_cells + train_cells + 1, j - train_cells - guard_cells : j + train_cells + guard_cells + 1]
            left = rdm_mag[i - guard_cells : i + guard_cells + 1, j - train_cells - guard_cells : j - guard_cells]
            right = rdm_mag[i - guard_cells : i + guard_cells + 1, j + guard_cells + 1 : j + guard_cells + train_cells + 1]
            
            noise_power = (np.sum(top) + np.sum(bottom) + np.sum(left) + np.sum(right)) / (train_cells * 4 * 2) # 平均
            
            threshold = noise_power * threshold_factor
            if rdm_mag[i, j] > threshold:
                detected[i, j] = True
                
    return detected