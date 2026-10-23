#!/usr/bin/env python3
"""Credential gate for any git publish path.

Scans content that is about to be committed and pushed, and fails loudly
if a credential is present.

Two independent checks:

  1. LITERAL check -- exact match against the credentials actually present
     on this machine (secrets/ files, service-env exports, credential
     reference files). These are read at run time. The values are never
     embedded in this script and never printed.

  2. PATTERN check -- credential-shaped strings that do not match any
     known literal. This catches keys that have rotated in, or that live
     somewhere the literal list does not cover.

Output is redacted: kind, path, and a short hash of the value. Never the
value itself.

Usage:
    secret-scan.py [REPO_DIR] [--staged | --worktree | --history RANGE] [--quiet]

Exit codes:
    0  clean
    1  findings (publication must be aborted)
    2  usage error
"""

import base64
import hashlib
import io
import json
import os
import plistlib
import re
import subprocess
import sys
import zipfile

MIN_LEN = 16
MAX_SCAN_BYTES = 64 * 1024 * 1024

# Third-party checkouts that live in the workspace. Their test fixtures
# contain deliberately fake tokens; they are skipped for PATTERN matching
# only. LITERAL matching always applies everywhere.
VENDOR_PREFIXES = (
    "paperclip/",
    "gbrain/",
    "nanobot/",
    "zeroclaw/",
    "ruvnet/",
    "AstrBot/",
    "nanoclaw/",
    "mental-health-bot/",
    "node_modules/",
    ".venv/",
    ".venv-ai-news/",
    "venv/",
    "dist/",
    "build/",
    "vendor/",
    "projects/",
    "target/",
)

# Build output and compiled artefacts. Random bytes match credential-shaped
# patterns often enough to make the gate cry wolf, so PATTERN matching skips
# these entirely. LITERAL matching still applies: a real key inside a binary
# is still a leak.
BINARY_SUFFIXES = (
    ".rlib",
    ".rmeta",
    ".dylib",
    ".so",
    ".dll",
    ".exe",
    ".o",
    ".a",
    ".wasm",
    ".class",
    ".jar",
    ".pdb",
    ".bin",
    ".dat",
    ".db",
    ".sqlite",
    ".npy",
    ".npz",
    ".onnx",
    ".pt",
    ".pth",
    ".safetensors",
)

SKIP_DIR_PARTS = (".git/", "node_modules/", "__pycache__/")

PATTERNS = (
    # The lookbehind matters: real keys are quoted or assigned, so they start
    # at a token boundary. Without it, "risk-update-2026-08-07" inside a URL
    # path matches "sk-update-..." and the gate cries wolf.
    ("openai-style-key", re.compile(rb"(?<![A-Za-z0-9])sk-[A-Za-z0-9_\-]{24,}")),
    ("github-classic-pat", re.compile(rb"(?<![A-Za-z0-9])ghp_[A-Za-z0-9]{30,}")),
    ("github-fine-pat", re.compile(rb"(?<![A-Za-z0-9])github_pat_[A-Za-z0-9_]{40,}")),
    ("github-oauth-token", re.compile(rb"(?<![A-Za-z0-9])gho_[A-Za-z0-9]{30,}")),
    ("github-app-token", re.compile(rb"(?<![A-Za-z0-9])ghs_[A-Za-z0-9]{30,}")),
    ("github-refresh-token", re.compile(rb"(?<![A-Za-z0-9])ghr_[A-Za-z0-9]{30,}")),
    ("agentmail-key", re.compile(rb"(?<![A-Za-z0-9])am_[A-Za-z0-9]{24,}")),
    ("slack-token", re.compile(rb"(?<![A-Za-z0-9])xox[baprs]-[A-Za-z0-9\-]{16,}")),
    ("google-api-key", re.compile(rb"(?<![A-Za-z0-9])AIza[0-9A-Za-z_\-]{30,}")),
    ("aws-access-key-id", re.compile(rb"(?<![A-Za-z0-9])(?:AKIA|ASIA)[0-9A-Z]{16}")),
    ("neuralia-secret", re.compile(rb"(?<![A-Za-z0-9])7eb[A-Za-z0-9]{40,}")),
    ("telegram-bot-token", re.compile(rb"(?<![A-Za-z0-9])\d{8,12}:[A-Za-z0-9_\-]{30,}")),
    ("anthropic-key", re.compile(rb"(?<![A-Za-z0-9])sk-ant-[A-Za-z0-9_\-]{24,}")),
)

# A matched value containing one of these is documentation, not a secret.
PLACEHOLDER_MARKERS = (
    "example",
    "your",
    "xxxx",
    "changeme",
    "placeholder",
    "redacted",
    "dummy",
    "fake",
    "sample",
    "notreal",
    "<",
    ">",
    "${",
)


def redact(value):
    raw = value if isinstance(value, bytes) else value.encode()
    return "sha256:%s len=%d" % (hashlib.sha256(raw).hexdigest()[:10], len(raw))


def looks_like_placeholder(value):
    low = value.lower()
    return any(marker in low for marker in PLACEHOLDER_MARKERS)


def is_binary(payload):
    """True if the payload looks like compiled/binary data."""
    if b"\x00" in payload[:8000]:
        return True
    return False


def in_url_context(payload, start, end):
    """True if the match sits inside a URL-ish token.

    A match inside "https://host/path/sk-update-2026" is prose, not a key.
    Checked on the whitespace-delimited token around the match.
    """
    left = start
    while left > 0 and payload[left - 1 : left] not in (b" ", b"\t", b"\n", b"\r", b'"', b"'", b"`"):
        left -= 1
    right = end
    limit = len(payload)
    while right < limit and payload[right : right + 1] not in (b" ", b"\t", b"\n", b"\r", b'"', b"'", b"`", b")", b"]", b","):
        right += 1
    token = payload[left:right]
    if b"://" in token:
        return True
    if token.lower().startswith((b"http", b"www.")):
        return True
    return False


def skip_pattern_matching(label):
    """True when PATTERN matching must be skipped for this path."""
    low = label.lower()
    if any(low.endswith(suffix) for suffix in BINARY_SUFFIXES):
        return True
    if "/target/" in low or "/build/" in low or "/dist/" in low:
        return True
    return False


# Environment variable names whose VALUES are credentials. A service env
# file holds plenty of non-secret values (launchd labels, Windows task names,
# PATH, ports). Treating every one of them as a credential literal made the
# gate abort on legitimate scripts that merely echo the launchd label.
CREDENTIAL_ENV_NAME = re.compile(
    r"(KEY|SECRET|TOKEN|PASSWORD|PASSWD|CREDENTIAL|PRIVATE|APIKEY)",
    re.I,
)


def plist_env_values(text):
    """Yield (key, value) pairs from a launchd plist EnvironmentVariables."""
    try:
        data = plistlib.loads(text.encode("utf-8", "ignore"))
    except Exception:
        return []
    env = data.get("EnvironmentVariables")
    if not isinstance(env, dict):
        return []
    return [(k, v) for k, v in env.items() if isinstance(v, str)]


def json_credential_values(node, prefix=""):
    """Yield (path, value) for credential-named string leaves in a JSON doc."""
    out = []
    if isinstance(node, dict):
        for key, value in node.items():
            path = prefix + "." + key if prefix else key
            if isinstance(value, str):
                if CREDENTIAL_ENV_NAME.search(key):
                    out.append((path, value))
            else:
                out.extend(json_credential_values(value, path))
    elif isinstance(node, list):
        for index, value in enumerate(node):
            out.extend(json_credential_values(value, "%s[%d]" % (prefix, index)))
    return out


def collect_literals():
    """Harvest credential values that exist on this machine."""
    literals = {}

    def add(kind, value):
        value = value.strip()
        if len(value) < MIN_LEN or looks_like_placeholder(value):
            return
        literals[(kind, value)] = hashlib.sha256(value.encode()).hexdigest()[:10]

    home = os.path.expanduser("~")

    # Overridable so the scanner can be tested without touching real keys.
    secrets_dir = os.environ.get(
        "OPENCLAW_SECRETS_DIR",
        os.path.join(home, ".openclaw", "workspace", "secrets"),
    )
    if os.path.isdir(secrets_dir):
        for name in sorted(os.listdir(secrets_dir)):
            path = os.path.join(secrets_dir, name)
            if not os.path.isfile(path):
                continue
            try:
                with open(path, "r", errors="ignore") as handle:
                    for line in handle:
                        line = line.strip()
                        if not line or line.startswith("#"):
                            continue
                        add("literal:secrets/" + name, line)
            except OSError:
                continue

    env_dir = os.environ.get(
        "OPENCLAW_SERVICE_ENV_DIR",
        os.path.join(home, ".openclaw", "service-env"),
    )
    if os.path.isdir(env_dir):
        for name in sorted(os.listdir(env_dir)):
            path = os.path.join(env_dir, name)
            if not os.path.isfile(path):
                continue
            try:
                with open(path, "r", errors="ignore") as handle:
                    for line in handle:
                        line = line.strip()
                        if line.startswith("export "):
                            line = line[len("export "):].strip()
                        if "=" not in line:
                            continue
                        key, _, value = line.partition("=")
                        value = value.strip().strip("\"'")
                        if not key or not value:
                            continue
                        if not CREDENTIAL_ENV_NAME.search(key):
                            continue
                        add("literal:service-env/" + key, value)
            except OSError:
                continue

    cred_ref = os.environ.get(
        "OPENCLAW_CREDENTIALS_REF",
        os.path.join(
            home,
            ".openclaw",
            "workspace",
            "agents",
            "dross",
            "references",
            "credentials.md",
        ),
    )
    if os.path.isfile(cred_ref):
        try:
            with open(cred_ref, "r", errors="ignore") as handle:
                for line in handle:
                    line = line.strip()
                    if ":" not in line:
                        continue
                    _, _, value = line.partition(":")
                    add("literal:credentials.md", value.strip().strip("`\"' "))
        except OSError:
            pass

    # LaunchAgent plists carry credentials in EnvironmentVariables. A key
    # that was rotated out of secrets/ but left behind in a plist is still a
    # credential. If the literal list does not know about it, the gate
    # reports "clean" on a repo that publishes it -- which is exactly how a
    # dead dev.to key survived in a public repository for months.
    plist_dir = os.environ.get(
        "OPENCLAW_LAUNCH_AGENTS_DIR",
        os.path.join(home, "Library", "LaunchAgents"),
    )
    if os.path.isdir(plist_dir):
        for name in sorted(os.listdir(plist_dir)):
            if not name.endswith(".plist"):
                continue
            path = os.path.join(plist_dir, name)
            try:
                with open(path, "r", errors="ignore") as handle:
                    text = handle.read()
            except OSError:
                continue
            for key, value in plist_env_values(text):
                # Only credential-named keys. A path like WACLI_STORE_DIR or
                # AGENT_MEMORY_DB is not a secret, and treating it as one
                # made the gate abort on legitimate backup content.
                if not CREDENTIAL_ENV_NAME.search(key):
                    continue
                add("literal:launchd/" + name + ":" + key, value)

    # The gateway config holds provider tokens under credential-named keys.
    config_path = os.environ.get(
        "OPENCLAW_CONFIG_PATH",
        os.path.join(home, ".openclaw", "openclaw.json"),
    )
    if os.path.isfile(config_path):
        try:
            with open(config_path, "r", errors="ignore") as handle:
                config = json.load(handle)
        except (OSError, ValueError):
            config = None
        if config is not None:
            for path, value in json_credential_values(config):
                add("literal:openclaw.json:" + path, value)

    return literals


def git(repo, *args):
    try:
        out = subprocess.run(
            ["git", "-C", repo] + list(args),
            capture_output=True,
            check=False,
        )
        return out.stdout
    except OSError:
        return b""


def git_ok(repo, *args):
    """Run a git command and report whether it succeeded.

    Used for commands whose failure must abort the scan. The plain git()
    helper swallows errors, which turns an unresolvable revision into
    "zero commits inspected" — and a scan that inspected nothing would
    otherwise report success. That is a fail-open, so anything that gates
    a push uses this instead.
    """
    try:
        out = subprocess.run(
            ["git", "-C", repo] + list(args),
            capture_output=True,
            check=False,
        )
    except OSError:
        return False, b""
    return out.returncode == 0, out.stdout


def candidate_files(repo, mode):
    """Files to inspect, relative to repo."""
    if mode == "staged":
        raw = git(repo, "diff", "--cached", "--name-only", "--diff-filter=ACMR")
    else:
        raw = git(repo, "ls-files", "--cached", "--others", "--exclude-standard")
    seen = []
    for line in raw.decode("utf-8", "replace").splitlines():
        name = line.strip()
        if not name:
            continue
        if any(part in name for part in SKIP_DIR_PARTS):
            continue
        if name not in seen:
            seen.append(name)
    return seen


def read_blob(repo, name, mode):
    """Return the bytes that would be published for this path."""
    if mode == "staged":
        spec = ":" + name
    else:
        spec = name
    try:
        out = subprocess.run(
            ["git", "-C", repo, "cat-file", "blob", spec],
            capture_output=True,
            check=False,
        )
    except OSError:
        return b""
    if out.returncode != 0:
        try:
            with open(os.path.join(repo, name), "rb") as handle:
                return handle.read(MAX_SCAN_BYTES)
        except OSError:
            return b""
    return out.stdout


def archive_members(data):
    """Yield (member_name, bytes) for zip payloads; empty otherwise."""
    if data[:4] != b"PK\x03\x04":
        return
    try:
        archive = zipfile.ZipFile(io.BytesIO(data))
    except Exception:
        return
    for member in archive.namelist():
        if member.endswith("/"):
            continue
        try:
            yield member, archive.read(member)
        except Exception:
            continue


def scan(repo, mode, quiet):
    literals = collect_literals()
    findings = []
    files = candidate_files(repo, mode)

    for name in files:
        data = read_blob(repo, name, mode)
        if not data:
            continue
        payloads = [(name, data)]
        for member, member_data in archive_members(data):
            payloads.append(("%s::%s" % (name, member), member_data))

        for label, payload in payloads:
            if len(payload) > MAX_SCAN_BYTES:
                payload = payload[:MAX_SCAN_BYTES]

            for (kind, value), digest in literals.items():
                if value.encode() in payload:
                    findings.append((kind, label, "sha256:" + digest))

            is_vendor = any(label.startswith(p) for p in VENDOR_PREFIXES)
            if is_vendor:
                continue
            if is_binary(payload):
                continue
            if skip_pattern_matching(label):
                continue
            for kind, pattern in PATTERNS:
                for match in pattern.finditer(payload):
                    try:
                        text = match.group(0).decode("utf-8", "ignore")
                    except Exception:
                        text = ""
                    if not text or looks_like_placeholder(text):
                        continue
                    if in_url_context(payload, match.start(), match.end()):
                        continue
                    findings.append(("pattern:" + kind, label, redact(text)))

    if findings and not quiet:
        print("SECRET-SCAN: ABORT - %d finding(s)" % len(findings))
        for kind, label, token in sorted(set(findings)):
            print("  %-34s %s  %s" % (kind, token, label))
        print("  Nothing was published. Remove the credential, then re-run.")
    elif findings:
        print("SECRET-SCAN: ABORT - %d finding(s)" % len(set(findings)))
    else:
        if not quiet:
            print("SECRET-SCAN: clean (%d file(s) inspected)" % len(files))

    return 1 if findings else 0


def scan_history(repo, rev_range, quiet):
    """Scan every blob reachable in a revision range.

    This is the check that matters at push time: it inspects the exact
    bytes that would become part of the published history, not just the
    files sitting in the working tree right now.

    rev_range may be a plain range ("main..HEAD"), a single rev ("HEAD",
    which means every ancestor of HEAD), or a list of either separated by
    commas.
    """
    literals = collect_literals()
    findings = []

    commits = []
    for part in rev_range.split(","):
        part = part.strip()
        if not part:
            continue
        ok, raw = git_ok(repo, "rev-list", part)
        if not ok:
            # An unresolvable range means we inspected nothing. Reporting
            # success here would let a push through unscanned.
            if not quiet:
                print(
                    "SECRET-SCAN: ABORT - could not resolve revision range %r"
                    % part
                )
                print("  Nothing was published. Fix the range, then re-run.")
            return 1
        commits.extend(raw.decode("utf-8", "replace").split())

    seen = set()
    for commit in commits:
        ok, tree = git_ok(repo, "ls-tree", "-r", commit)
        if not ok:
            if not quiet:
                print(
                    "SECRET-SCAN: ABORT - could not read tree for commit %s"
                    % commit
                )
                print("  Nothing was published. Fix the range, then re-run.")
            return 1
        for line in tree.decode("utf-8", "replace").splitlines():
            parts = line.split(None, 3)
            if len(parts) < 4 or parts[1] != "blob":
                continue
            seen.add((parts[2], parts[3]))

    for sha, name in sorted(seen):
        data = git(repo, "cat-file", "blob", sha)
        if not data:
            continue
        payloads = [(name, data)]
        for member, member_data in archive_members(data):
            payloads.append(("%s::%s" % (name, member), member_data))
        for label, payload in payloads:
            if len(payload) > MAX_SCAN_BYTES:
                payload = payload[:MAX_SCAN_BYTES]
            for (kind, value), digest in literals.items():
                if value.encode() in payload:
                    findings.append((kind, label, "sha256:" + digest))
            is_vendor = any(label.startswith(p) for p in VENDOR_PREFIXES)
            if is_vendor or is_binary(payload) or skip_pattern_matching(label):
                continue
            for kind, pattern in PATTERNS:
                for match in pattern.finditer(payload):
                    try:
                        text = match.group(0).decode("utf-8", "ignore")
                    except UnicodeDecodeError:
                        text = ""
                    if not text or looks_like_placeholder(text):
                        continue
                    if in_url_context(payload, match.start(), match.end()):
                        continue
                    findings.append(("pattern:" + kind, label, redact(text)))

    if findings and not quiet:
        print("SECRET-SCAN: ABORT - %d finding(s) in %s" % (len(findings), rev_range))
        for kind, label, token in sorted(set(findings)):
            print("  %-34s %s  %s" % (kind, token, label))
        print("  Nothing was published. Remove the credential, then re-run.")
    elif findings:
        print("SECRET-SCAN: ABORT - %d finding(s) in %s" % (len(set(findings)), rev_range))
    else:
        if not quiet:
            print(
                "SECRET-SCAN: clean (%d blob(s) inspected in %s)"
                % (len(seen), rev_range)
            )

    return 1 if findings else 0


def main(argv):
    # Parse argv by hand: --history takes a value that may or may not look
    # like a flag, so a flags/values split cannot work.
    repo = None
    mode = "staged"
    quiet = False
    history_range = None
    argv = list(argv[1:])
    i = 0
    while i < len(argv):
        arg = argv[i]
        if arg in ("-h", "--help"):
            print(__doc__)
            return 2
        if arg == "--worktree":
            mode = "worktree"
        elif arg == "--staged":
            mode = "staged"
        elif arg == "--quiet":
            quiet = True
        elif arg == "--history":
            if i + 1 >= len(argv):
                print(
                    "secret-scan: --history needs a revision range",
                    file=sys.stderr,
                )
                return 2
            history_range = argv[i + 1]
            i += 1
        elif arg.startswith("--history="):
            history_range = arg.split("=", 1)[1]
        elif arg.startswith("-"):
            print("secret-scan: unknown option %s" % arg, file=sys.stderr)
            return 2
        elif repo is None:
            repo = arg
        else:
            print(
                "secret-scan: unexpected argument %s" % arg, file=sys.stderr
            )
            return 2
        i += 1

    repo = os.path.abspath(repo) if repo else os.getcwd()
    if not os.path.isdir(os.path.join(repo, ".git")):
        print("secret-scan: not a git repo: %s" % repo, file=sys.stderr)
        return 2
    if history_range:
        return scan_history(repo, history_range, quiet)
    return scan(repo, mode, quiet)


if __name__ == "__main__":
    sys.exit(main(sys.argv))
