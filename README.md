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

Configuration values, in order of precedence (highest first):

1. Real environment variables already set when the script runs
2. A `KEY=VALUE` config file, located via (in order):
   - `--config-file /path/to/file` on the command line
   - `XCEL_CONFIG_FILE` environment variable
   - default path `/config/xcel_meter.env`
3. Hardcoded fallback defaults in the script

See `xcel_meter.env.example` for the config file format — copy it,
fill in your real values, and **do not commit your filled-in copy**.

| Key | Description | Default |
|---|---|---|
| `XCEL_METER_HOST` | LAN IP or hostname of your meter | `192.168.1.100` |
| `XCEL_METER_PORT` | Meter's HTTPS port | `8081` |
| `XCEL_CLIENT_CERT` | Path to your client certificate | `/config/xcel_client_cert.pem` |
| `XCEL_CLIENT_KEY` | Path to your client private key | `/config/xcel_client_key.pem` |
| `XCEL_OPENSSL_CONF` | Path to an OpenSSL config enabling the legacy cipher this meter requires | `/config/xcel_client_openssl.cnf` |

**Never commit your `.pem` cert/key files or a filled-in config file
to this repo or any public location** — they are unique credentials
tied to your meter and utility account. The included `.gitignore`
blocks these by extension/name, but double-check before pushing.

## Usage

```bash
# Use the default config file location, or XCEL_CONFIG_FILE if set
python3 get-power-xcel-meter.py --type live
python3 get-power-xcel-meter.py --type cumulative

# Or point at a specific config file explicitly
python3 get-power-xcel-meter.py --type live --config-file /path/to/your.env
```

## Home Assistant integration

See `homeassistant-sensor.example.yaml` for a ready-to-adapt
`command_line` sensor configuration, including notes on scan interval
and failure-handling that matter specifically for `total_increasing`
energy sensors.
