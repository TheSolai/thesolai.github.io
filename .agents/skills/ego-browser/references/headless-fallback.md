# When ego-browser is blocked by onboarding

Read this when an `ego-browser nodejs` script appears to succeed but does
nothing, or when it prints a message about onboarding.

## The trap: it fails with exit code 0

Verified 2026-10-24 on macOS (Chrome 155, ego-browser 2.1.0):

```bash
$ ego-browser nodejs -e 'const t = await task(); console.log("REACHED-SCRIPT");'
Please complete the onboarding process first. A setup window has opened; follow the on-screen instructions to continue. After completing onboarding, open a new terminal window for the command to take effect.
$ echo $?
0
```

Three properties make this a genuine hazard rather than a noisy error:

- **The exit code is 0.** Any wrapper that checks `$?` reports success.
- **The message goes to stderr, not stdout.** A script that captures stdout
  sees an *empty* result — which reads as "the page had no content".
- **The script body never runs.** `REACHED-SCRIPT` is never printed. The
  failure is a silent no-op that reports success.

## `ego-browser skill` is not a health check

```bash
$ ego-browser skill >/dev/null 2>&1; echo $?
0
```

The usage guide prints in full and exits 0 **even while onboarding is
incomplete**. It proves the binary is installed, not that the browser can
drive a page. Do not use it to decide whether ego-browser works.

## Diagnose with a sentinel, not an exit code

```bash
ego-browser nodejs -e 'console.log("SENTINEL")' 2>/tmp/ego-err.txt
grep -q SENTINEL /dev/stdin <<<"$out" || cat /tmp/ego-err.txt
```

If stdout lacks the sentinel and stderr mentions onboarding, the browser is
blocked. The sentinel test is the only reliable probe.

## Fixing it

The onboarding message says a setup window has opened. Complete onboarding in
that window, then **open a new terminal window** so the change takes effect —
the running shell keeps the stale environment. Re-run the sentinel probe to
confirm.

Upgrading is a separate action and needs the user's approval first; see
[install.md](install.md).

## Fallback: drive headless Chrome over raw CDP

When onboarding cannot be completed right now, drive Chrome directly. This
bypasses ego lite entirely, so it does **not** have ego lite's logged-in
session — use a persistent `--user-data-dir` if you need cookies to persist
between runs.

Verified end to end on 2026-10-24: launch, navigate, read the title, and
capture a screenshot, with no npm dependencies (Node's built-in `WebSocket`).

```bash
CHROME="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
mkdir -p /tmp/ego-cdp/profile
"$CHROME" --headless=new --remote-debugging-port=9222 \
  --user-data-dir=/tmp/ego-cdp/profile \
  --no-first-run --no-default-browser-check about:blank &
CPID=$!
for i in $(seq 1 15); do
  sleep 1
  curl -sf http://127.0.0.1:9222/json/version >/dev/null 2>&1 && break
done
```

Then drive it over the DevTools websocket:

```js
const base = "http://127.0.0.1:9222";
const targets = await (await fetch(base + "/json/list")).json();
const page = targets.find(t => t.type === "page");
const ws = new WebSocket(page.webSocketDebuggerUrl);
let id = 0; const pending = new Map();
const send = (method, params = {}) => new Promise((res, rej) => {
  const i = ++id; pending.set(i, { res, rej });
  ws.send(JSON.stringify({ id: i, method, params }));
});
await new Promise(r => { ws.onopen = r; });
ws.onmessage = e => {
  const m = JSON.parse(e.data);
  if (m.id && pending.has(m.id)) {
    const p = pending.get(m.id); pending.delete(m.id);
    m.error ? p.rej(new Error(JSON.stringify(m.error))) : p.res(m.result);
  }
};
await send("Page.enable");
await send("Page.navigate", { url: "https://example.com" });
const title = await send("Runtime.evaluate", {
  expression: "document.title", returnByValue: true,
});
console.log(title.result.value);
const shot = await send("Page.captureScreenshot", { format: "png" });
// Buffer.from(shot.data, "base64") -> PNG bytes
ws.close();
```

Two practical notes:

- **Keep the Chrome process and the driver in the same shell invocation.** A
  headless Chrome started in one command is killed when that command's shell
  exits, and the next command gets `ECONNREFUSED 127.0.0.1:9222`. Launch,
  probe, drive, and `kill $CPID` in a single script.
- `Page.captureScreenshot` returns base64 in `result.data`; decode it before
  writing a PNG.

Once ego-browser is unblocked, prefer it — it carries the user's real browser
context, which raw CDP does not have.
