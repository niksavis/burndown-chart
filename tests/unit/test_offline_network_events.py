import subprocess
import sys

import pytest


@pytest.mark.parametrize(
    "operation",
    [
        "socket.gethostbyname('example.com')",
        "socket.gethostbyname_ex('example.com')",
        "socket.gethostbyaddr('192.0.2.1')",
        "socket.getnameinfo(('192.0.2.1', 443), 0)",
    ],
)
def test_external_dns_entrypoints_are_refused_before_resolution(operation: str) -> None:
    source = """
import socket
import sys
from utils.offline import install_offline_policy, OfflineNetworkError
install_offline_policy()
assert socket.gethostbyname('localhost') == '127.0.0.1'
try:
    exec(sys.argv[1])
except OfflineNetworkError:
    print('refused')
else:
    raise SystemExit('external DNS was allowed')
"""
    result = subprocess.run(
        [sys.executable, "-", operation],
        input=source,
        capture_output=True,
        text=True,
        timeout=10,
        check=True,
    )
    assert result.stdout.strip() == "refused"
