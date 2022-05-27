import numpy as np
import numpy.typing as npt

from rfind_web.network import SIOClient

from .base import DataProviderBase


class DataProviderSIOBase(DataProviderBase):
    def __init__(self) -> None:
        super().__init__()

        self.connect()

    def connect(self) -> None:
        self.sio = SIOClient()

    def emit_integration(
        self, timestamp: float, integration: npt.NDArray[np.int16]
    ) -> None:
        self.sio.emit(
            event="integration",
            data={"timestamp": timestamp, "bins": integration.tobytes()},
        )
