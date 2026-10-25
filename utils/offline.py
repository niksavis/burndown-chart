import ipaddress
import sys
from typing import Any


class OfflineNetworkError(RuntimeError):
    pass


def is_loopback(host: str | bytes | None) -> bool:
    if host is None:
        return True
    if isinstance(host, bytes):
        host = host.decode("ascii")
    if host.lower() == "localhost":
        return True
    try:
        return ipaddress.ip_address(host).is_loopback
    except ValueError:
        return False


def require_local_network(event: str, arguments: tuple[Any, ...]) -> None:
    host = None
    if event == "socket.getaddrinfo":
        host = arguments[0]
    elif event in {"socket.connect", "socket.bind", "socket.sendto"}:
        address = arguments[1]
        if isinstance(address, tuple):
            host = address[0]
    else:
        return
    if not is_loopback(host):
        raise OfflineNetworkError("Network access is disabled in the demo workspace")


def install_offline_policy() -> None:
    sys.addaudithook(require_local_network)
