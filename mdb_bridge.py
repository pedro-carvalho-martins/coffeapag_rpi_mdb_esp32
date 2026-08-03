#!/usr/bin/env python3
"""Minimal Raspberry Pi client for the ESP32 MDB cashless bridge."""

from __future__ import annotations

import argparse
import re
import sys

import serial
from serial import SerialException


VEND_REQUEST_RE = re.compile(r"^MDB VEND_REQUEST price=(\d+) item=(\d+)$")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Start an MDB session and approve or deny ESP32 vend requests."
    )
    parser.add_argument(
        "--port",
        default="/dev/serial0",
        help="Serial device (default: /dev/serial0 for Raspberry Pi GPIO UART)",
    )
    parser.add_argument(
        "--baud",
        type=int,
        default=115200,
        help="Serial baud rate (default: 115200)",
    )
    parser.add_argument(
        "--funds",
        type=int,
        default=500,
        help="Session funds in MDB minor units (default: 500, normally 5.00)",
    )
    parser.add_argument(
        "--decision",
        choices=("deny", "approve", "prompt"),
        default="deny",
        help="Vend decision policy (default: deny)",
    )
    args = parser.parse_args()

    if not 0 <= args.funds <= 0xFFFF:
        parser.error("--funds must be between 0 and 65535")
    if args.baud <= 0:
        parser.error("--baud must be greater than zero")

    return args


def send_command(connection: serial.Serial, command: str) -> None:
    connection.write(f"{command}\n".encode("ascii"))
    connection.flush()
    print(f"> {command}", flush=True)


def choose_decision(policy: str, price: int, item: int) -> str:
    if policy == "approve":
        return "APPROVE"
    if policy == "deny":
        return "DENY"

    answer = input(f"Approve item {item} at price {price}? [y/N]: ").strip().lower()
    return "APPROVE" if answer in {"y", "yes"} else "DENY"


def run(args: argparse.Namespace) -> int:
    try:
        with serial.Serial(args.port, args.baud, timeout=1) as connection:
            print(f"Connected to {args.port} at {args.baud} baud", flush=True)
            send_command(connection, f"SESSION {args.funds}")

            while True:
                raw_line = connection.readline()
                if not raw_line:
                    continue

                line = raw_line.decode("utf-8", errors="replace").strip()
                if not line:
                    continue

                print(f"< {line}", flush=True)
                match = VEND_REQUEST_RE.match(line)
                if match:
                    price, item = (int(value) for value in match.groups())
                    send_command(connection, choose_decision(args.decision, price, item))
    except KeyboardInterrupt:
        print("\nStopped", flush=True)
        return 0
    except SerialException as error:
        print(f"Serial error: {error}", file=sys.stderr)
        return 1


def main() -> int:
    return run(parse_args())


if __name__ == "__main__":
    raise SystemExit(main())
