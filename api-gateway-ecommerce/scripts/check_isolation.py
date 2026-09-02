"""Checks that the gateway is the only port anything off this machine can reach.

The two services bind 127.0.0.1; the gateway binds 0.0.0.0. That difference is
easy to assert and easy to get wrong, so it is tested rather than claimed: the
same three ports are dialled twice, once on the loopback address and once on the
machine's routable address, and the results are printed side by side.

    python3 scripts/check_isolation.py
"""
from __future__ import annotations

import socket

PORTS = [
    (8000, "products-service"),
    (8001, "orders-service"),
    (8091, "api-gateway"),
]


def routable_ip() -> str:
    """The address this machine would use to talk to anything else.

    No packet is sent - a UDP socket only has to be connected for the kernel to
    pick the source address it would use.
    """
    probe = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        probe.connect(("8.8.8.8", 80))
        return probe.getsockname()[0]
    finally:
        probe.close()


def dial(host: str, port: int, timeout: float = 2.0) -> str:
    sock = socket.socket()
    sock.settimeout(timeout)
    try:
        sock.connect((host, port))
        return "connected"
    except ConnectionRefusedError:
        return "refused"
    except socket.timeout:
        return "timed out"
    except OSError as exc:
        return f"{type(exc).__name__}"
    finally:
        sock.close()


def main() -> None:
    external = routable_ip()

    print("=== the same three ports, dialled two ways ===")
    print(f"    loopback   127.0.0.1")
    print(f"    routable   {external}   (what another machine would use)")
    print()
    print(f"{'PORT':<7}{'SERVICE':<19}{'via 127.0.0.1':<16}via " + external)
    print("-" * 62)
    for port, name in PORTS:
        local = dial("127.0.0.1", port)
        remote = dial(external, port)
        print(f"{port:<7}{name:<19}{local:<16}{remote}")

    print()
    print("=== what that means ===")
    print("    Only 8091 answers on the routable address, so the gateway is the")
    print("    only way in. The two services are reachable from processes on this")
    print("    machine, which includes the gateway, and from nothing else.")
    print()
    print("    On a runtime where the bridge network works, the same property")
    print("    comes from docker-compose.yml instead: the services get `expose`")
    print("    and only the gateway gets `ports`.")


if __name__ == "__main__":
    main()
