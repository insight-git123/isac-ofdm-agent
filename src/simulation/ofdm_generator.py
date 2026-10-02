"""OFDM 波形生成器：基于 Task1 提取的 numerology 参数生成时域信号。"""
import numpy as np

class OFDMGenerator:
    def __init__(self, scs_khz: float, cp_duration_us: float, fft_size: int = 1024):
        self.scs_khz = scs_khz
        self.cp_duration_us = cp_duration_us
        self.fft_size = fft_size
        # 采样率 = 子载波间隔 * FFT点数
        self.sampling_rate = scs_khz * 1e3 * fft_size
        # CP 样本数 = CP时长 * 采样率
        self.cp_samples = int(np.round(cp_duration_us * 1e-6 * self.sampling_rate))

    def generate(self, num_symbols: int = 2):
        """生成 OFDM 时域波形 (CP + IFFT数据)"""
        waveforms = []
        for _ in range(num_symbols):
            # 1. 生成频域 QPSK 随机符号
            freq_data = (np.random.randn(self.fft_size) + 1j * np.random.randn(self.fft_size)) / np.sqrt(2)
            
            # 2. IFFT 变换到时域
            time_data = np.fft.ifft(freq_data) * np.sqrt(self.fft_size)
            
            # 3. 添加循环前缀 (CP)
            cp = time_data[-self.cp_samples:]
            ofdm_symbol = np.concatenate([cp, time_data])
            waveforms.append(ofdm_symbol)
        
        return np.concatenate(waveforms)