"""Task3: 频域多目标 ISAC 雷达模型 + RDM + Swerling-I + TDL 多径。"""
import numpy as np


class RadarSimulator:
    def __init__(self, scs_khz: float, fft_size: int = 1024,
                 num_symbols: int = 64, fc_ghz: float = 3.5):
        self.fft_size = fft_size
        self.num_symbols = num_symbols
        self.fc_ghz = fc_ghz
        self.c = 3e8
        self.scs = scs_khz * 1e3
        self.bandwidth = fft_size * self.scs
        self.symbol_duration = 1 / self.scs

    def generate_echo(self, targets: list, snr_db: float = 20,
                      use_swerling: bool = False, use_multipath: bool = False):
        """
        频域多目标回波，含时延/多普勒/RCS/可选 Swerling-I/可选 TDL 多径。
        targets: [{"range": m, "velocity": m/s, "rcs": float}, ...]
        """
        X = (np.random.randn(self.fft_size, self.num_symbols) +
             1j * np.random.randn(self.fft_size, self.num_symbols)) / np.sqrt(2)

        k = np.arange(self.fft_size).reshape(-1, 1)     # 子载波索引
        l = np.arange(self.num_symbols).reshape(1, -1)  # 符号索引

        Y = np.zeros_like(X)

        # 多径配置 (额外时延ns, 相对衰减dB, 相对速度m/s)
        if use_multipath:
            paths = [
                (0,    0.0,   0.0),     # 直接路径 (LOS)
                (50,  -3.0,   5.0),     # 多径1
                (150, -8.0, -10.0),     # 多径2
            ]
        else:
            paths = [(0, 0.0, 0.0)]     # 仅 LOS

        for tgt in targets:
            mean_rcs = tgt.get("rcs", 1.0)
            tau_base = 2 * tgt["range"] / self.c
            fd_base = 2 * tgt["velocity"] * self.fc_ghz * 1e9 / self.c

            for (delay_ns, atten_db, dv) in paths:
                tau = tau_base + delay_ns * 1e-9
                fd = fd_base + 2 * dv * self.fc_ghz * 1e9 / self.c
                path_rcs = mean_rcs * (10 ** (atten_db / 10))

                if use_swerling:
                    # Swerling-I: 整个 CPI 内该路径的 RCS 恒定
                    rcs_scalar = np.random.exponential(scale=path_rcs)
                    amp = np.sqrt(rcs_scalar)
                else:
                    amp = np.sqrt(path_rcs)

                phase_range = -2 * np.pi * k * self.scs * tau
                phase_doppler = 2 * np.pi * l * self.symbol_duration * fd
                Y += amp * X * np.exp(1j * (phase_range + phase_doppler))

        # 加高斯白噪声
        sig_pow = np.mean(np.abs(Y) ** 2)
        noise_pow = sig_pow / (10 ** (snr_db / 10))
        Y += (np.random.randn(*Y.shape) + 1j * np.random.randn(*Y.shape)) * np.sqrt(noise_pow / 2)

        return X, Y

    def compute_rdm(self, X, Y):
        """信道估计 + 2D-FFT 得到距离-多普勒图。"""
        H = Y * np.conj(X) / (np.abs(X) ** 2 + 1e-12)
        range_profile = np.fft.ifft(H, axis=0)
        rdm = np.fft.fftshift(np.fft.fft(range_profile, axis=1), axes=1)
        rdm_mag = np.abs(rdm)

        range_axis = np.arange(self.fft_size) * self.c / (2 * self.bandwidth)
        doppler_freq = np.fft.fftshift(np.fft.fftfreq(
            self.num_symbols, d=self.symbol_duration))
        velocity_axis = doppler_freq * self.c / (2 * self.fc_ghz * 1e9)

        return rdm_mag, range_axis, velocity_axis