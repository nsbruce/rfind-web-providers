from typing import Dict, Union

import socketio  # type: ignore # TODO check whether stubs/types are available

from rfind_web.environment import load_env


class SIOClient:
    """
    SocketIO client
    """

    def __init__(self, debug: bool = False) -> None:
        """
        Initialize the client
        """
        self.env = load_env()

        self.sio = socketio.Client(
            ssl_verify=self.env["SOCKETIO_PROTOCOL"] == "https",
            logger=debug,
            engineio_logger=debug,
        )
        self.addr = (
            self.env["SOCKETIO_PROTOCOL"]
            + "://"
            + self.env["SOCKETIO_IP"]
            + ":"
            + self.env["SOCKETIO_PORT"]
        )
        self.sio.connect(self.addr, namespaces=[self.env["SOCKETIO_BACKEND_NAMESPACE"]])
        self.__register_handlers__()

    def emit(self, event: str, data: Dict[str, Union[str, float, bytes]]) -> None:
        """
        Emit a socketio event
        TODO type for data might need to be changed
        """
        self.sio.emit(
            event=event, data=data, namespace=self.env["SOCKETIO_BACKEND_NAMESPACE"]
        )

    def __register_handlers__(self) -> None:
        """
        Register the event handlers
        """
        self.sio.on("connect", self.on_connect)
        self.sio.on("disconnect", self.on_disconnect)

    def on_connect(self) -> None:
        """
        Handle the connection event
        """
        print("I connected to the server")

    def on_disconnect(self) -> None:
        """
        Handle the disconnection event
        """
        print("I am disconnected from the server")

    def wait(self) -> None:
        """
        Wait for the socketio connection to be established
        """
        self.sio.wait()
