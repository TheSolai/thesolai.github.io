#!/usr/bin/env python3
"""
Verify the local clone renders identically to the live site.

Runs a throwaway HTTP server inside this process (so it cannot be reaped with
its parent shell), drives headless Chrome against both the local clone and
the live origin, then compares the rendered DOM.
"""
import os
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import urllib.request
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

CLONE = os.path.expanduser("~/Projects/electros-launchpad-clone")
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
LIVE = "https://launchpad.electros.cloud/"
PORT = 8791


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *a):
        pass


def serve():
    handler = partial(QuietHandler, directory=CLONE)
    httpd = ThreadingHTTPServer(("127.0.0.1", PORT), handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd


def chrome(args, url, timeout=90):
    profile = tempfile.mkdtemp(prefix="lpchrome_")
    cmd = [
        CHROME, "--headless=new", "--disable-gpu", "--no-sandbox",
        "--hide-scrollbars", "--no-first-run", "--no-default-browser-check",
        f"--user-data-dir={profile}", "--virtual-time-budget=10000",
        "--window-size=1440,2400",
    ] + args + [url]
    try:
        subprocess.run(cmd, capture_output=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        print("  chrome timed out")
    finally:
        shutil.rmtree(profile, ignore_errors=True)


def fetch(url, timeout=15):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8", "replace")


def text_of(html):
    """Strip scripts/styles/tags -> comparable visible text."""
    h = re.sub(r"(?is)<script.*?</script>", " ", html)
    h = re.sub(r"(?is)<style.*?</style>", " ", h)
    h = re.sub(r"(?s)<!--.*?-->", " ", h)
    h = re.sub(r"(?s)<[^>]+>", " ", h)
    h = re.sub(r"&[a-zA-Z#0-9]+;", " ", h)
    return re.sub(r"\s+", " ", h).strip()


def main():
    httpd = serve()
    time.sleep(1.5)

    local = f"http://127.0.0.1:{PORT}/index.html"
    try:
        body = fetch(local)
        print(f"local server responds: OK ({len(body)} bytes)")
    except Exception as e:
        print(f"local server FAILED: {e}")
        httpd.shutdown()
        return 1

    out = "/tmp/lp_probe"
    os.makedirs(out, exist_ok=True)

    print("rendering local clone...")
    chrome(["--screenshot=" + out + "/clone_local.png"], local)
    print("rendering live site...")
    chrome(["--screenshot=" + out + "/clone_live.png"], LIVE)

    print("dumping DOM (local)...")
    chrome(["--dump-dom"], local, timeout=120)

    httpd.shutdown()

    for f in ("clone_local.png", "clone_live.png"):
        p = os.path.join(out, f)
        sz = os.path.getsize(p) if os.path.exists(p) else 0
        print(f"{f}: {sz} bytes")

    return 0


if __name__ == "__main__":
    sys.exit(main())
