# Raspberry Pi MDB-ESP32 Test Client

This is a minimal Raspberry Pi client for the local serial protocol exposed by
the `mdb-pi-bridge-esp32s3` firmware.

## Wiring

Use a 3.3 V USB-to-TTL adapter connected to a Raspberry Pi USB port:

```text
ESP32 GPIO17 (TX) -> adapter RXD
ESP32 GPIO18 (RX) -> adapter TXD
ESP32 GND         -> adapter GND
```

Leave the adapter's `5V`, `VCC`, and `3V3` pins disconnected. The ESP32 should
continue to receive its intended power separately.

## Raspberry Pi setup

```bash
sudo apt update
sudo apt install -y python3-venv
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements.txt
```

Find the adapter device:

```bash
ls -l /dev/ttyUSB* /dev/ttyACM* 2>/dev/null
```

A CH340 adapter will normally appear as `/dev/ttyUSB0`. If access is denied,
add the current user to `dialout`, then sign out and back in:

```bash
sudo usermod -aG dialout "$USER"
```

## Safe first test

The default decision is DENY, so no product should be dispensed:

```bash
python mdb_bridge.py --port /dev/ttyUSB0 --funds 500
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
python mdb_bridge.py --port /dev/ttyUSB0 --funds 500 --decision approve
```

For a manual decision, use `--decision prompt`. Respond quickly because the VMC
may impose a short cashless response timeout.

Stop the client with `Ctrl+C`.
