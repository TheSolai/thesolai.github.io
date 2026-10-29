#!/usr/bin/env python3
"""Runtime configuration for the delivery recipients.

The two delivery addresses are NOT stored in this repository. They are read
at run time from a machine-local file that git ignores:

    skills/zlib-kindle/state/recipients.json

    {
      "kindle": "<amazon send-to-kindle address>",
      "gmail": "<gmail address>"
    }

Why they are not in the tracked source: the publish gate treats an address
that appears under secrets/ as a credential literal and refuses to publish
a working tree, an index, or a commit that contains one. Reading the
addresses at run time keeps the literal out of the source without
weakening the gate and without an exception list for it. The scanner still
collects the literal, still scans every tracked file, and still blocks if
it ever appears in one.

The file must exist before a delivery run. A missing or malformed file is
a hard error: refusing to guess is safer than delivering a library to an
address nobody chose.

Override the location with ZLIB_KINDLE_RECIPIENTS if the config lives
somewhere else.
"""

import json
import os

DEFAULT_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "state",
    "recipients.json",
)

# The order matters: callers unpack (kindle, gmail) positionally.
KEYS = ("kindle", "gmail")


class ConfigError(RuntimeError):
    """The recipient configuration is missing or malformed."""


def path():
    """Where the recipient configuration is read from."""
    return os.environ.get("ZLIB_KINDLE_RECIPIENTS") or DEFAULT_PATH


def load(config_path=None):
    """Return (kindle, gmail) from the runtime configuration.

    Raises ConfigError if the file is missing, unparseable, or does not
    carry both addresses. Never falls back to a built-in default.
    """
    target = config_path or path()
    try:
        with open(target, encoding="utf-8") as handle:
            data = json.load(handle)
    except OSError as exc:
        raise ConfigError(
            "cannot read delivery recipients from %s: %s" % (target, exc)
        ) from exc
    except ValueError as exc:
        raise ConfigError(
            "delivery recipients at %s are not valid JSON: %s" % (target, exc)
        ) from exc

    if not isinstance(data, dict):
        raise ConfigError(
            "delivery recipients at %s must be a JSON object" % target
        )

    addresses = []
    for key in KEYS:
        value = data.get(key)
        if not isinstance(value, str) or "@" not in value:
            raise ConfigError(
                "delivery recipients at %s: missing or malformed '%s' address"
                % (target, key)
            )
        addresses.append(value.strip())

    return tuple(addresses)


def as_csv(config_path=None):
    """The recipients as a comma-separated string, for --to style flags."""
    return ",".join(load(config_path))
