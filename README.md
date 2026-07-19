# xcel-meter-reader

Reads live and cumulative power data from an Xcel Energy smart meter's
local HAN (Home Area Network) HTTPS interface, for use with Home
Assistant's `command_line` sensor or standalone.

## How it works

Xcel smart meters expose a local HTTPS API on the home network,
authenticated via a mutual TLS client certificate issued during meter
registration. This script queries that API directly — no cloud
round-trip, no dependency on Xcel's customer portal being up.

## Requirements

- A client certificate and private key issued for your specific meter
  (obtained through Xcel's meter registration/enrollment process —
  not covered by this repo)
- `curl` available on `PATH`
- Python 3.10+

## Configuration

Set these environment variables (or edit the defaults in the script):

| Variable | Description | Default |
|---|---|---|
| `XCEL_METER_HOST` | LAN IP or hostname of your meter | `192.168.1.100` |
| `XCEL_METER_PORT` | Meter's HTTPS port | `8081` |
| `XCEL_CLIENT_CERT` | Path to your client certificate | `/config/xcel_client_cert.pem` |
| `XCEL_CLIENT_KEY` | Path to your client private key | `/config/xcel_client_key.pem` |
| `XCEL_OPENSSL_CONF` | Path to an OpenSSL config enabling the legacy cipher this meter requires | `/config/xcel_client_openssl.cnf` |

**Never commit your `.pem` cert/key files or OpenSSL config to this
repo or any public location** — they are unique credentials tied to
your meter and utility account. The included `.gitignore` blocks
these by extension, but double-check before pushing.

## Usage

```bash
python3 get-power-xcel-meter.py --type live
python3 get-power-xcel-meter.py --type cumulative
```

## Home Assistant integration

Example `command_line` sensor config (adjust paths/env as needed):

```yaml
command_line:
  - sensor:
      name: Xcel Meter Consumption
      command: "python3 /config/get-power-xcel-meter.py --type cumulative"
      unit_of_measurement: "Wh"
      state_class: total_increasing
      scan_interval: 60
```

Note the `total_increasing` state class — this tells HA's recorder
the value should only ever go up. If your sensor briefly returns an
error or an unexpected value, HA may interpret that as a meter reset
and adjust its long-term statistics accordingly. Make sure your
command's failure mode is a clean non-zero exit rather than error
text on stdout, or you may see phantom spikes/drops in your Energy
dashboard history.
