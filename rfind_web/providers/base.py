import numpy as np
import numpy.typing as npt

from rfind_web.environment import load_env


class DataProviderBase:
    def __init__(self) -> None:
        self.env = load_env()

    def connect(self) -> None:
        raise NotImplementedError

    def get_integration(self) -> npt.NDArray[np.int16]:
        raise NotImplementedError

    def emit_integration(
        self, timestamp: float, integration: npt.NDArray[np.int16]
    ) -> None:
        raise NotImplementedError

    def run(self) -> None:
        raise NotImplementedError
