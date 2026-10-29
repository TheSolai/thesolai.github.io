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
                   [--baseline REV]

    --baseline REV names a revision that is ALREADY PUBLISHED. Literal
    credential values that already occur in that revision's tree are
    reported as pre-existing and do not block the scan; every other
    finding still does. A credential that is new to the baseline is still
    fatal, so this only stops the gate re-blocking on content it published
    long ago. Pattern findings are never suppressed.

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
import tempfile
import threading
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


def is_vendor_path(label):
    """True when the path sits inside a vendored third-party checkout.

    The check has to recognise the vendor directory wherever it appears in
    the path, not only at the very start. The private backup repo stores its
    copy of the workspace under `workspace/`, so a vendored checkout lives at
    `workspace/projects/vellum-rs/...` and a plain `startswith("projects/")`
    test misses it entirely. That is what made the publish gate reject
    ~1.5 GB of third-party material: the vendored trees were scanned for
    credential *patterns*, their fake test fixtures tripped every pattern,
    and the push was blocked.

    Component-boundary matching fixes it without weakening the guard:

      - PATTERN matching is skipped for vendored paths only.
      - LITERAL matching (the real credential values) still runs everywhere,
        including inside vendor trees. A genuine key inside a vendored
        checkout is still a leak and still blocks the push.
    """
    for prefix in VENDOR_PREFIXES:
        if label.startswith(prefix) or ("/" + prefix) in label:
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


def _read_disk(repo, name):
    """Read a file from the working tree, capped at MAX_SCAN_BYTES."""
    try:
        with open(os.path.join(repo, name), "rb") as handle:
            return handle.read(MAX_SCAN_BYTES)
    except OSError:
        return b""


def _batch_blobs(repo, specs):
    """Yield (spec, data) for each object spec using ONE `git cat-file --batch`.

    Reading blobs one subprocess at a time costs a process spawn per file.
    On a repo with ~5,600 tracked files, and again for every blob reachable
    in the pushed range, that is thousands of spawns — several minutes of
    wall clock. That is long enough that `git push` hits its own timeout
    *inside* this hook, before the credential scan has even finished.

    `git cat-file --batch` takes a list of object names on stdin and writes
    one response per name, in order, so a single process can serve an
    entire scan. The bytes it returns are identical to `git cat-file blob`.

    Yields (spec, data), where data is None when git cannot resolve the
    spec; the caller decides whether to fall back to reading from disk.

    Only one blob is held in memory at a time — a full history of this repo
    is ~490 MB, which must not be buffered.
    """
    specs = list(specs)
    if not specs:
        return

    try:
        proc = subprocess.Popen(
            ["git", "-C", repo, "cat-file", "--batch"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
        )
    except OSError:
        for spec in specs:
            yield spec, None
        return

    def feed():
        # Writing on a helper thread keeps the pipe from deadlocking: git
        # writes responses while we are still sending names.
        try:
            for spec in specs:
                proc.stdin.write(spec.encode("utf-8", "replace") + b"\n")
            proc.stdin.flush()
        except (BrokenPipeError, ValueError, OSError):
            pass
        finally:
            try:
                proc.stdin.close()
            except (BrokenPipeError, ValueError, OSError):
                pass

    writer = threading.Thread(target=feed, daemon=True)
    writer.start()

    out = proc.stdout
    try:
        for spec in specs:
            header = out.readline()
            if not header:
                break
            parts = header.split()
            if len(parts) < 3:
                # "<spec> missing" — git could not resolve this object.
                yield spec, None
                continue
            try:
                size = int(parts[2])
            except (TypeError, ValueError):
                yield spec, None
                continue
            data = out.read(size)
            if data is None:
                data = b""
            out.read(1)  # the newline that terminates the payload
            yield spec, data
    finally:
        writer.join(timeout=30)
        try:
            out.close()
        except OSError:
            pass
        try:
            proc.wait(timeout=10)
        except Exception:
            proc.kill()


def _index_shas(repo):
    """Map of path -> blob sha for the current index (stage 0 only)."""
    raw = git(repo, "ls-files", "-s")
    result = {}
    for line in raw.decode("utf-8", "replace").splitlines():
        if not line.strip():
            continue
        meta, _, path = line.partition("\t")
        parts = meta.split()
        if len(parts) < 3:
            continue
        sha, stage = parts[1], parts[2]
        if stage != "0":
            continue
        result[path] = sha
    return result


def read_blob(repo, name, mode):
    """Return the bytes that would be published for this path.

    Kept for compatibility; the scanners below use the batched reader.
    """
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
        return _read_disk(repo, name)
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


def _baseline_contains(repo, rev, value):
    """True when `value` occurs in the tree of revision `rev`.

    The value is passed to git through a pattern file, never on the command
    line: a command line is visible to every process on the machine and
    lands in shell history, and a credential must not do either.

    Fails closed. A git error returns False, which leaves the finding
    blocking rather than silently suppressing it.
    """
    fd, path = tempfile.mkstemp(prefix="secret-scan-", suffix=".pattern")
    try:
        os.write(fd, value.encode() + b"\n")
        os.close(fd)
        os.chmod(path, 0o600)
        proc = subprocess.run(
            ["git", "-C", repo, "grep", "-F", "-q", "-f", path, rev, "--"],
            capture_output=True,
            check=False,
        )
        return proc.returncode == 0
    except OSError:
        return False
    finally:
        try:
            os.unlink(path)
        except OSError:
            pass


def published_literal_digests(repo, rev, literals, wanted):
    """Which of `wanted` literal digests already occur in revision `rev`.

    A credential that is already published in the baseline is pre-existing
    exposure, not a new leak. Refusing the push does not unpublish it, and a
    gate that blocks forever on it stops guarding anything real — that is
    exactly what stranded the private backup, where the reply address had
    been published across 41 files long before the gate ever ran.

    Only the exact literal values already present in the baseline are
    treated as pre-existing. A value that is not in the baseline still
    blocks the push, so a newly introduced credential is still fatal.

    Returns (found_digests, baseline_readable). When the baseline cannot be
    read, nothing is suppressed: the scan fails closed.
    """
    if not wanted:
        return set(), True
    ok, _ = git_ok(repo, "rev-parse", "--verify", "%s^{commit}" % rev)
    if not ok:
        return set(), False

    found = set()
    for (_kind, value), digest in literals.items():
        if digest not in wanted:
            continue
        if _baseline_contains(repo, rev, value):
            found.add(digest)
    return found, True


def split_published(repo, findings, literals, baseline):
    """Split findings into (blocking, already_published).

    Only LITERAL findings can be baselined: a pattern match is a shape, not
    a value, and the baseline is searched for exact literal values only.
    A pattern finding therefore always blocks.
    """
    if not baseline or not findings:
        return findings, []

    wanted = set()
    for kind, _label, token in findings:
        if kind.startswith("literal:") and token.startswith("sha256:"):
            wanted.add(token.split(":", 1)[1])

    if not wanted:
        return findings, []

    published, readable = published_literal_digests(
        repo, baseline, literals, wanted
    )
    if not readable:
        # Fail closed: an unreadable baseline must not silently suppress.
        return findings, []
    if not published:
        return findings, []

    blocking = []
    preexisting = []
    for finding in findings:
        kind, label, token = finding
        if (
            kind.startswith("literal:")
            and token.startswith("sha256:")
            and token.split(":", 1)[1] in published
        ):
            preexisting.append(finding)
        else:
            blocking.append(finding)
    return blocking, preexisting


def _check_payloads(label, data, literals, findings, vendor_ok=True):
    """Apply the literal and pattern checks to one blob and its archive members."""
    if not data:
        return
    payloads = [(label, data)]
    for member, member_data in archive_members(data):
        payloads.append(("%s::%s" % (label, member), member_data))

    for payload_label, payload in payloads:
        if len(payload) > MAX_SCAN_BYTES:
            payload = payload[:MAX_SCAN_BYTES]

        for (kind, value), digest in literals.items():
            if value.encode() in payload:
                findings.append((kind, payload_label, "sha256:" + digest))

        if is_vendor_path(payload_label):
            continue
        if is_binary(payload):
            continue
        if skip_pattern_matching(payload_label):
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
                findings.append(("pattern:" + kind, payload_label, redact(text)))


def scan(repo, mode, quiet, baseline=None):
    literals = collect_literals()
    findings = []
    files = candidate_files(repo, mode)

    if mode == "staged":
        # The index content for each staged path, read in one batch.
        index_shas = _index_shas(repo)
        specs = []
        for name in files:
            sha = index_shas.get(name)
            specs.append(sha if sha else ":" + name)
        blobs = {}
        for spec, data in _batch_blobs(repo, specs):
            blobs[spec] = data
        for name, spec in zip(files, specs):
            data = blobs.get(spec)
            if not data:
                data = _read_disk(repo, name)
            _check_payloads(name, data, literals, findings)
    else:
        # The working tree: the bytes that would be published are the ones
        # on disk right now.
        #
        # The original implementation asked git for `cat-file blob <path>`,
        # which is not a valid object name in git 2.x — every call failed and
        # the scan fell back to reading the file from disk. This is that
        # behaviour, minus 5,600 subprocess spawns.
        #
        # Reading the disk copy is also the stricter check: it sees
        # uncommitted edits, which the index copy would not.
        for name in files:
            _check_payloads(name, _read_disk(repo, name), literals, findings)

    blocking, preexisting = split_published(repo, findings, literals, baseline)

    if preexisting and not quiet:
        print(
            "SECRET-SCAN: %d finding(s) already published in the baseline "
            "(pre-existing, not blocking)" % len(set(preexisting))
        )
    if blocking and not quiet:
        print("SECRET-SCAN: ABORT - %d finding(s)" % len(blocking))
        for kind, label, token in sorted(set(blocking)):
            print("  %-34s %s  %s" % (kind, token, label))
        print("  Nothing was published. Remove the credential, then re-run.")
    elif blocking:
        print("SECRET-SCAN: ABORT - %d finding(s)" % len(set(blocking)))
    else:
        if not quiet:
            print("SECRET-SCAN: clean (%d file(s) inspected)" % len(files))

    return 1 if blocking else 0


def scan_history(repo, rev_range, quiet, baseline=None):
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

    # One blob read for the whole range, streamed so only a single blob is
    # held in memory at a time (the full history of a busy site is ~490 MB).
    name_for_sha = {}
    for sha, name in sorted(seen):
        name_for_sha.setdefault(sha, name)

    for sha, data in _batch_blobs(repo, list(name_for_sha.keys())):
        if not data:
            continue
        _check_payloads(name_for_sha.get(sha, sha), data, literals, findings)

    blocking, preexisting = split_published(repo, findings, literals, baseline)

    if preexisting and not quiet:
        print(
            "SECRET-SCAN: %d finding(s) already published in the baseline "
            "(pre-existing, not blocking)" % len(set(preexisting))
        )
    if blocking and not quiet:
        print("SECRET-SCAN: ABORT - %d finding(s) in %s" % (len(blocking), rev_range))
        for kind, label, token in sorted(set(blocking)):
            print("  %-34s %s  %s" % (kind, token, label))
        print("  Nothing was published. Remove the credential, then re-run.")
    elif blocking:
        print("SECRET-SCAN: ABORT - %d finding(s) in %s" % (len(set(blocking)), rev_range))
    else:
        if not quiet:
            print(
                "SECRET-SCAN: clean (%d blob(s) inspected in %s)"
                % (len(seen), rev_range)
            )

    return 1 if blocking else 0


def main(argv):
    # Parse argv by hand: --history takes a value that may or may not look
    # like a flag, so a flags/values split cannot work.
    repo = None
    mode = "staged"
    quiet = False
    history_range = None
    baseline = None
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
        elif arg == "--baseline":
            if i + 1 >= len(argv):
                print(
                    "secret-scan: --baseline needs a revision",
                    file=sys.stderr,
                )
                return 2
            baseline = argv[i + 1]
            i += 1
        elif arg.startswith("--baseline="):
            baseline = arg.split("=", 1)[1]
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
        return scan_history(repo, history_range, quiet, baseline)
    return scan(repo, mode, quiet, baseline)


if __name__ == "__main__":
    sys.exit(main(sys.argv))
