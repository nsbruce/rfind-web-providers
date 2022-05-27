import datetime
import time
from typing import Generator

import numpy as np
import numpy.typing as npt

from .base_sio import DataProviderSIOBase


class DataProviderSim(DataProviderSIOBase):
    def __init__(self) -> None:
        super().__init__()

        self.fcs = [0.25e9, 0.85e9, 1e9, 1.2e9, 1.3e9, 1.55e9]
        self.fms = [
            (0.3e9, 200e3),
            (0.5e9, 10e6),
            (0.9e9, 10e6),
            (1.1e9, 10e6),
            (1.25e9, 35e6),
            (1.4e9, 200e3),
            (1.5e9, 20e6),
        ]

        self.t_int = float(self.env["INTEGRATION_RATE"])
        self.nbins = int(self.env["N_BINS"])

        self.outMin = float(self.env["SPECTRA_MIN_VALUE"])
        outMax = float(self.env["SPECTRA_MAX_VALUE"])
        self.outDiff = outMax - self.outMin

        self.generator = self.spec_gen(noise_pwr=1.0)

    def __shift_signals__(self) -> None:
        """
        Shifts the signals to be around DC instead of around fs/2
        """

        # Shift everything down because we're going to build a complex spectra
        self.fcs = [fc - float(self.env["BANDWIDTH"]) / 2 for fc in self.fcs]
        self.fms = [(fc - float(self.env["BANDWIDTH"]) / 2, bw) for fc, bw in self.fms]

    def __FM__(
        self, fc: float, BW: float, t_arr: npt.NDArray[np.float32]
    ) -> npt.NDArray[np.float32]:
        BW /= 2
        fm = 1e5
        Am = 1
        mt = Am * np.cos(2 * np.pi * fm * t_arr)
        beta = BW / fm
        Ac = 1
        st = Ac * np.exp(1j * (2 * np.pi * fc * t_arr + beta * mt))
        return np.array(st)

    def spec_gen(
        self, noise_pwr: float
    ) -> Generator[npt.NDArray[np.float32], None, None]:
        t_incr = 0.0
        while True:
            t_arr = np.linspace(t_incr, t_incr + self.t_int, self.nbins)

            output = np.random.normal(
                0, np.sqrt(noise_pwr), self.nbins
            ) + 1j * np.random.normal(0, np.sqrt(noise_pwr), self.nbins)

            for fc in self.fcs:
                output += np.exp(2j * np.pi * fc * t_arr)

            for fc, bw in self.fms:
                output += self.__FM__(fc, bw, t_arr)

            output = np.abs(np.fft.fftshift(np.fft.fft(output)))

            output /= np.max(output)

            yield np.array(output)
            t_incr += self.t_int

    def get_integration(self) -> npt.NDArray[np.int16]:
        spec = next(self.generator)
        spec *= 10 ** (self.outDiff / 10)
        spec += 10 ** (self.outMin / 10)

        spec = np.array(1000.0 * np.log10(spec)).astype(dtype=np.int16)

        return np.array(spec)

    def run(self) -> None:
        while True:
            start = time.time()

            integration = self.get_integration()
            ts = datetime.datetime.now().timestamp() * 1000

            try:
                self.emit_integration(
                    timestamp=ts,
                    integration=integration,
                )
                print("Integration emitted")
            except Exception as e:
                print("Integration not emitted:", e)

            looptime = time.time() - start
            time.sleep(self.t_int - looptime)


def start() -> None:
    """
    Starts the data provider
    """
    provider = DataProviderSim()
    provider.run()
