"""Task3: 雷达回波模拟与距离-多普勒处理 (ISAC 感知核心)。"""
import numpy as np

class RadarSimulator:
    def __init__(self, scs_khz: float, fft_size: int = 1024, num_symbols: int = 64, fc_ghz: float = 3.5):
        self.scs_khz = scs_khz
        self.fft_size = fft_size
        self.num_symbols = num_symbols
        self.fc_ghz = fc_ghz # 载波频率 GHz
        
        self.c = 3e8 # 光速
        self.subcarrier_spacing = scs_khz * 1e3
        self.bandwidth = self.fft_size * self.subcarrier_spacing
        self.symbol_duration = 1 / self.subcarrier_spacing
        
    def generate_echo(self, target_range: float, target_velocity: float, snr_db: float = 20):
        """生成目标回波信号 (频域)"""
        # 1. 基础 OFDM 频域数据 (全1导频，简化处理)
        X = np.ones((self.fft_size, self.num_symbols), dtype=complex)
        
        # 2. 计算时延和多普勒频移
        tau = 2 * target_range / self.c                     # 时延 (s)
        fd = 2 * target_velocity * self.fc_ghz * 1e9 / self.c # 多普勒频移 (Hz)
        
        # 3. 构造回波: Y = X * exp(-j*2*pi*k*df*tau) * exp(j*2*pi*l*Tsym*fd)
        k = np.arange(self.fft_size).reshape(-1, 1) # 子载波索引
        l = np.arange(self.num_symbols).reshape(1, -1) # 符号索引
        
        phase_range = -2 * np.pi * k * self.subcarrier_spacing * tau
        phase_doppler = 2 * np.pi * l * self.symbol_duration * fd
        
        Y = X * np.exp(1j * (phase_range + phase_doppler))
        
        # 4. 添加高斯白噪声
        signal_power = np.mean(np.abs(Y)**2)
        noise_power = signal_power / (10 ** (snr_db / 10))
        noise = (np.random.randn(*Y.shape) + 1j * np.random.randn(*Y.shape)) * np.sqrt(noise_power / 2)
        
        return Y + noise

    def compute_rdm(self, Y: np.ndarray):
        """计算距离-多普勒图 (Range-Doppler Map)"""
        # 1. 距离维处理: 对子载波维做 IFFT (频域 -> 时域/距离)
        range_profile = np.fft.ifft(Y, axis=0)
        
        # 2. 多普勒维处理: 对符号维做 FFT (慢时间 -> 多普勒)
        rdm = np.fft.fftshift(np.fft.fft(range_profile, axis=1), axes=1)
        
        # 3. 计算坐标轴
        # 距离轴: c * k / (2 * BW)
        range_axis = np.arange(self.fft_size) * self.c / (2 * self.bandwidth)
        # 速度轴: 多普勒频率 -> 速度
        doppler_axis = np.fft.fftshift(np.fft.fftfreq(self.num_symbols, d=self.symbol_duration))
        velocity_axis = doppler_axis * self.c / (2 * self.fc_ghz * 1e9)
        
        return rdm, range_axis, velocity_axis