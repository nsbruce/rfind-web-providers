import datetime
import multiprocessing
import re
import uuid
import warnings

import Calibration
import numpy as np
import numpy.typing as npt
import ostore
import rastro.data_feed
import rastro.time_prefix
from dateutil.parser import isoparse

from .base_sio import DataProviderSIOBase


class DataProviderS3(DataProviderSIOBase):
    def __init__(self) -> None:
        super().__init__()

        self.prev_dt = None
        self.spec = np.zeros((16, 37500))
        self.count = 0
        self.freq_hz = np.linspace(0e6, 2000e6, 600000)

        self.__setup_cal__()

    def __setup_cal__(self) -> None:
        self.noise_on_fname = "noise_on.dat"
        self.noise_off_fname = "noise_off.dat"

        self.p_on: npt.NDArray[np.float32] = np.fromfile(
            self.noise_on_fname, dtype=np.float32
        )
        self.p_off: npt.NDArray[np.float32] = np.fromfile(
            self.noise_off_fname, dtype=np.float32
        )
        self.coeffs = Calibration.get_cal_coeffs(self.freq_hz, self.p_on, self.p_off)

        self.inCalCycle = False
        self.savedOnCal = True
        self.savedOffCal = True

    def __setup_database__(self) -> None:
        self.object_name = "test-object-from-script-" + str(uuid.uuid4())
        config = ostore.Config.load(self.env["NX_S3_CONFIG_JSON"])
        self.storage = ostore.ObjectStore(config)
        key_queue = multiprocessing.Queue()

        self.key_streamer = multiprocessing.Process(
            target=self.__get_keys__, args=(key_queue, "rfind")
        )

    def start_streaming(self) -> None:
        self.key_streamer.start()

    def stop_streaming(self) -> None:
        self.key_streamer.terminate()

    def __get_keys__(self, queue, key_prefix) -> None:
        generator = rastro.time_prefix.TimePrefixGenerator(5.0, "seconds")

        keys = rastro.data_feed.keys_from_prefixes(
            self.storage,
            rastro.data_feed.add_prefix(
                key_prefix, generator.generate_prefixes(multiprocessing.Event())
            ),
        )
        for key in keys:
            queue.put(key)

    def __set_cal_state__(self, timeObj: datetime.datetime) -> None:
        # Decide whether to save new calibration data or use the existing one
        if timeObj.minute == 1 and not self.inCalCycle and not self.savedOnCal:
            self.inCalCycle = True
            self.savedOnCal = False  # Already set to false but still valid
            self.savedOffCal = False  # Already set to false but still valid
        if timeObj.minute > 3 and (not self.savedOnCal or not self.savedOffCal):
            raise warnings.Warning(
                "Calibration cycle ended and calibrations were not saved"
            )

    def get_integration(self, timeObj: datetime.datetime) -> npt.NDArray[np.int16]:

        if (timeObj - self.prev_dt).total_seconds() > 1:
            print("-- Dropped Data?")

        full_spec = np.roll(np.reshape(self.spec, -1), -18750)

        if self.inCalCycle and timeObj.minute == 1 and not self.savedOnCal:
            # Save uncalibrated spectrum
            self.p_on = full_spec.astype(np.float32)
            self.p_on.tofile(self.noise_on_fname)
            self.savedOnCal = True
        if self.inCalCycle and timeObj.minute == 2 and not self.savedOffCal:
            self.p_off = full_spec.astype(np.float32)
            self.p_off.tofile(self.noise_off_fname)
            self.savedOffCal = True
        if timeObj.minute == 3 and self.inCalCycle:
            self.coeffs = Calibration.get_cal_coeffs(
                self.freq_hz, self.p_on, self.p_off
            )
            self.inCalCycle = False
            self.savedOnCal = False  # resetting for next time
            self.savedOffCal = False  # resetting for next time

        full_spec = Calibration.apply_cal(full_spec, self.coeffs)
        return (1000 * np.log10(full_spec / 0.001))[60000:-60000].astype("int16")

    def run(self) -> None:
        self.start_streaming()
        while True:

            key = self.key_queue.get()
            match = re.search(self.env["NX_S3_REGEX"], key)

            if match:
                timestamp = match.group(1)
                timeObj = isoparse(timestamp)
                sl = int(match.group(2))
                ch = int(match.group(3))
                if ch == 1:
                    sl += 8

                self.__set_cal_state__(timeObj)

                if sl in np.arange(2, 15):
                    if self.prev_dt is not None:
                        if (timeObj - self.prev_dt).total_seconds() > 0:
                            bins = self.get_integration(timeObj)

                            try:
                                self.emit_integration(
                                    timestamp=timestamp,
                                    integration=bins,
                                )
                                print("Integration emitted")
                            except Exception as e:
                                print("Integration not emitted:", e)

                            self.prev_dt = timeObj
                            self.count = 0

                        data = np.frombuffer(
                            self.storage.get(key).data, dtype=np.int64
                        ).astype("float32")
                        self.spec[sl] = 10.0 * np.log10(data[1250:-1250])
                        self.count += 1
                    else:
                        self.prev_dt = timeObj


def start() -> None:
    """
    Starts the data provider
    """
    provider = DataProviderS3()

    try:
        provider.run()

    except KeyboardInterrupt:
        provider.stop_streaming()
        pass
