#!/usr/bin/env python3
"""
Fetch live or cumulative power data from an Xcel Energy smart meter's
local HAN (Home Area Network) HTTPS interface, authenticated via
mutual TLS using the client certificate issued for your meter.

Requires:
  - A client certificate + private key issued for your meter
    (obtain via Xcel's meter registration process; not covered here)
  - curl available on PATH

Usage:
  python3 get-power-xcel-meter.py --type live
  python3 get-power-xcel-meter.py --type cumulative

Configuration is via environment variables (see README) so no
personal network details or credential paths are hardcoded here.
"""

import argparse
import os
import re
import subprocess
import sys

# --- Optional config file support ---
# Config values can come from (in order of precedence, highest first):
#   1. Real environment variables already set when the script runs
#   2. KEY=VALUE lines in a config file (--config-file, or XCEL_CONFIG_FILE
#      env var, or the default path below)
#   3. Hardcoded defaults
DEFAULT_CONFIG_FILE_PATH = "/config/xcel_meter.env"


def load_config_file(path: str) -> None:
    if not path or not os.path.isfile(path):
        return
    try:
        with open(path, "r") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, _, value = line.partition("=")
                key = key.strip()
                value = value.strip().strip('"').strip("'")
                # Don't override a value that's already set as a real
                # environment variable — env vars win over the file.
                os.environ.setdefault(key, value)
    except OSError as e:
        print(f"Warning: could not read config file {path}: {e}", file=sys.stderr)

# Meter endpoint paths — these are fixed by the meter's firmware/API,
# not personal to any install, so they stay as constants.
ENDPOINTS = {
    "live": "/upt/1/mr/1/r",
    "cumulative": "/upt/1/mr/3/r",
}


def fetch_data(url: str, cert_path: str, key_path: str, openssl_conf_path: str) -> str | None:
    env = os.environ.copy()
    env["OPENSSL_CONF"] = openssl_conf_path

    for path, label in [(cert_path, "client cert"), (key_path, "client key")]:
        if not os.path.isfile(path):
            print(f"Error: {label} not found at {path}. "
                  f"Set the appropriate environment variable or config file entry.", file=sys.stderr)
            return None

    curl_command = [
        "curl",
        "--ciphers", "ECDHE-ECDSA-AES128-CCM8",
        "--insecure",
        "--url", url,
        "--cert", cert_path,
        "--key", key_path,
    ]

    try:
        result = subprocess.run(
            curl_command, capture_output=True, text=True, env=env,
            check=True, timeout=15,
        )
    except subprocess.CalledProcessError as e:
        print(f"Error executing curl (exit {e.returncode}): {e.stderr.strip()}", file=sys.stderr)
        return None
    except subprocess.TimeoutExpired:
        print("Error: request to meter timed out", file=sys.stderr)
        return None

    extracted_values = re.findall(r"<value>(.*?)</value>", result.stdout)
    numbers = [num for value in extracted_values for num in re.findall(r"[0-9]+", value)]

    if not numbers:
        print("Warning: no values parsed from meter response", file=sys.stderr)
        return None

    return "\n".join(numbers)


def main():
    parser = argparse.ArgumentParser(
        description="Fetch data from a local Xcel smart meter HAN interface."
    )
    parser.add_argument(
        "--type", required=True, choices=list(ENDPOINTS.keys()),
        help="Type of data to fetch",
    )
    parser.add_argument(
        "--config-file",
        default=None,
        help=(
            "Path to a KEY=VALUE config file. Overrides XCEL_CONFIG_FILE "
            f"env var and the default path ({DEFAULT_CONFIG_FILE_PATH}) if given."
        ),
    )
    args = parser.parse_args()

    # Precedence for which config file to load:
    # 1. --config-file on the command line
    # 2. XCEL_CONFIG_FILE environment variable
    # 3. DEFAULT_CONFIG_FILE_PATH
    config_file = args.config_file or os.environ.get("XCEL_CONFIG_FILE", DEFAULT_CONFIG_FILE_PATH)
    load_config_file(config_file)

    # Read final config values now that the file (if any) has been loaded
    # into the environment. Real env vars set before the script ran still
    # take precedence over anything in the file.
    meter_host = os.environ.get("XCEL_METER_HOST", "192.168.1.100")
    meter_port = os.environ.get("XCEL_METER_PORT", "8081")
    cert_path = os.environ.get("XCEL_CLIENT_CERT", "/config/xcel_client_cert.pem")
    key_path = os.environ.get("XCEL_CLIENT_KEY", "/config/xcel_client_key.pem")
    openssl_conf_path = os.environ.get("XCEL_OPENSSL_CONF", "/config/xcel_client_openssl.cnf")

    url = f"https://{meter_host}:{meter_port}{ENDPOINTS[args.type]}"
    output = fetch_data(url, cert_path, key_path, openssl_conf_path)

    if output is None:
        sys.exit(1)

    print(output)


if __name__ == "__main__":
    main()
