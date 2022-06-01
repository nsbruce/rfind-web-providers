import datetime
import time

import numpy as np
import numpy.typing as npt
import uhd

from .base_sio import DataProviderSIOBase


class DataProviderUSRP(DataProviderSIOBase):
    def __init__(self, gain: float = 15.0) -> None:
        super().__init__()

        self.t_int = float(self.env["INTEGRATION_RATE"])
        self.nbins = int(self.env["N_BINS"])

        self.fs = float(self.env["BANDWIDTH"])
        f0 = float(self.env["START_FREQ"])
        f1 = f0 + self.fs
        self.fc = (f0 + f1) / 2

        self.gain = gain

        self.samples: npt.NDArray[np.complex64] = np.empty(
            (1, self.nbins), dtype=np.complex64
        )

        self.setup_usrp()

    def setup_usrp(self) -> None:
        self.usrp = uhd.usrp.MultiUSRP()
        self.usrp.set_rx_rate(self.fs, 0)
        self.usrp.set_rx_freq(self.fc, 0)
        self.usrp.set_rx_gain(self.gain, 0)

        st_args = uhd.usrp.StreamArgs("fc32", "sc16")
        st_args.channels = [0]

        self.metadata = uhd.types.RXMetadata()
        self.streamer = self.usrp.get_rx_stream(st_args)
        buffer_samps = self.streamer.get_max_num_samps()
        self.recv_buffer: npt.NDArray[np.complex64] = np.zeros(
            (1, buffer_samps), dtype=np.complex64
        )  # dtype here correlates with the "fc32" stream arg

    def start_streaming(self) -> None:
        stream_cmd = uhd.types.StreamCMD(uhd.types.StreamMode.start_cont)
        stream_cmd.stream_now = True
        self.streamer.issue_stream_cmd(stream_cmd)

    def stop_streaming(self) -> None:
        stream_cmd = uhd.types.StreamCMD(uhd.types.StreamMode.stop_cont)
        self.streamer.issue_stream_cmd(stream_cmd)

    def __PSD__(self, samples: npt.NDArray[np.complex64]) -> npt.NDArray[np.float32]:
        """
        Calculates the Power Spectral Density of the samples
        """
        window = np.hamming(len(samples))
        result = np.multiply(window, samples)
        result = np.fft.fftshift(np.fft.fft(result, self.nbins))
        # Multiply by extra 100 so we can int it later
        result = np.abs(np.nan_to_num(1000.0 * np.log10(np.square(np.abs(result)))))
        result = np.abs(result)
        return np.array(result)

    def get_integration(self) -> npt.NDArray[np.int16]:
        recv_samps = 0
        while recv_samps < self.nbins:
            samps = self.streamer.recv(self.recv_buffer, self.metadata)
            if self.metadata.error_code != uhd.types.RXMetadataErrorCode.none:
                print(self.metadata.strerror())
            if samps:
                real_samps = min(self.nbins - recv_samps, samps)
                self.samples[
                    :, recv_samps : recv_samps + real_samps
                ] = self.recv_buffer[:, 0:real_samps]
                recv_samps += real_samps
        # Compute PSD
        bins: npt.NDArray[np.int16] = self.__PSD__(self.samples).astype(np.int16)

        return np.array(bins)

    def run(self) -> None:

        self.start_streaming()
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
    provider = DataProviderUSRP()

    try:
        provider.run()

    except KeyboardInterrupt:
        provider.stop_streaming()
        pass
