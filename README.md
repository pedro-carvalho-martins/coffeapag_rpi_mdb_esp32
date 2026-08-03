# Raspberry Pi MDB-ESP32 Test Client

This is a minimal Raspberry Pi client for the local serial protocol exposed by
the `mdb-pi-bridge-esp32s3` firmware.

## Wiring

The minimal ESP32 firmware repurposes the board's exposed I2C header as a 3.3 V
UART because I2C is not used:

```text
ESP32 SDA / GPIO10 (TX) -> Raspberry Pi GPIO15/RXD, physical pin 10
ESP32 SCL / GPIO11 (RX) -> Raspberry Pi GPIO14/TXD, physical pin 8
ESP32 GND               -> Raspberry Pi GND, physical pin 6 or another GND
```

Leave the ESP32 `3V3`, `VIN`, and `PULSE` pins disconnected. Power down both
devices before attaching or removing GPIO wiring.

## Raspberry Pi setup

```bash
sudo apt update
sudo apt install -y python3-venv
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements.txt
```

Enable the Raspberry Pi UART with `sudo raspi-config`. Under `Interface Options`
and `Serial Port`, disable the login shell and enable the serial hardware, then
reboot. Confirm the UART device:

```bash
ls -l /dev/serial0
```

If access is denied, add the current user to `dialout`, then sign out and back in:

```bash
sudo usermod -aG dialout "$USER"
```

## Safe first test

The default decision is DENY, so no product should be dispensed:

```bash
python mdb_bridge.py --funds 500
```

The expected sequence includes:

```text
> SESSION 500
< ACK SESSION funds=500
< MDB SESSION_BEGIN funds=500
< MDB VEND_REQUEST price=... item=...
> DENY
```

## Approval test

Only use this when the machine is ready to dispense a real product:

```bash
python mdb_bridge.py --funds 500 --decision approve
```

For a manual decision, use `--decision prompt`. Respond quickly because the VMC
may impose a short cashless response timeout.

Stop the client with `Ctrl+C`.
