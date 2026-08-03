#!/usr/bin/env python3
"""Interactive vend test for the ESP32 MDB cashless bridge."""

from __future__ import annotations

import argparse
import re
import sys

import serial
from serial import SerialException


VEND_REQUEST_RE = re.compile(r"^MDB VEND_REQUEST price=(\d+) item=(\d+)$")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Display each selected product and approve or deny it with y/n."
    )
    parser.add_argument("--port", default="/dev/serial0")
    parser.add_argument("--baud", type=int, default=115200)
    parser.add_argument(
        "--funds",
        type=int,
        default=500,
        help="Session funds in MDB minor units (default: 500, normally 5.00)",
    )
    parser.add_argument(
        "--decimals",
        type=int,
        default=2,
        help="Digits after the decimal point when displaying prices (default: 2)",
    )
    args = parser.parse_args()

    if not 0 <= args.funds <= 0xFFFF:
        parser.error("--funds must be between 0 and 65535")
    if args.baud <= 0:
        parser.error("--baud must be greater than zero")
    if not 0 <= args.decimals <= 3:
        parser.error("--decimals must be between 0 and 3")

    return args


def send_command(connection: serial.Serial, command: str) -> None:
    connection.write(f"{command}\n".encode("ascii"))
    connection.flush()
    print(f"> {command}", flush=True)


def format_price(raw_price: int, decimals: int) -> str:
    if decimals == 0:
        return str(raw_price)
    divisor = 10**decimals
    return f"{raw_price / divisor:.{decimals}f}"


def ask_for_decision(item: int, raw_price: int, decimals: int) -> str:
    shown_price = format_price(raw_price, decimals)
    print(
        f"\nCustomer selected item {item}, price {shown_price} "
        f"(raw MDB value {raw_price}).",
        flush=True,
    )

    while True:
        answer = input("Approve sale? [y/n]: ").strip().lower()
        if answer in {"y", "yes"}:
            return "APPROVE"
        if answer in {"n", "no"}:
            return "DENY"
        print("Please type y or n.", flush=True)


def run(args: argparse.Namespace) -> int:
    try:
        with serial.Serial(args.port, args.baud, timeout=1) as connection:
            print(f"Connected to {args.port} at {args.baud} baud", flush=True)
            send_command(connection, f"SESSION {args.funds}")
            print("Waiting for the customer to select a product...", flush=True)

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
                    decision = ask_for_decision(item, price, args.decimals)
                    send_command(connection, decision)
                    print("Waiting for the vending-machine result...", flush=True)
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
