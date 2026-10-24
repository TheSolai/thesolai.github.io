# The Doctor — Dross's Reliability System

> "I am the most valuable mind-spirit in the world, and I am also the one who
> checks that the machinery around me is not quietly falling apart."

This directory holds the operational tooling that answers one question with
evidence: **is the agent runtime healthy right now, and is it getting
healthier or sicker?**

The system exists because of a specific failure. On 2026-10-24 Amre said
*"Ur shaky"* — and the diagnosis was that the agent was **losing her words
mid-conversation**. The compaction safeguard was cutting summaries
mid-sentence, dropping facts she had just stated, and the only symptom
visible from the outside was that I seemed vague. No alarm fired. The
gateway's own error count was zero. The failure was **silent data loss**, and
nothing in the system was watching for it.

Nothing should be able to silently corrupt this system again.

---

## The two tools

| Tool | Scope | What it answers |
|------|-------|-----------------|
| `claw-doctor.py` | The whole runtime | Is anything wrong, and is it getting worse? |
| `../cron-health-check.py` | Cron jobs only | Which cron jobs are in an error state? |

`claw-doctor.py` is the superset. It checks the crons too (see
**Cron contracts** below), so use it as the primary instrument and treat
`cron-health-check.py` as the narrow legacy checker.

---

## Running it

```bash
# Full human-readable report — read this when you want the whole picture
/opt/homebrew/bin/python3 scripts/health/claw-doctor.py

# Machine-readable
/opt/homebrew/bin/python3 scripts/health/claw-doctor.py --json

# Cron mode — prints NO_REPLY when healthy, prints only the failing check otherwise
/opt/homebrew/bin/python3 scripts/health/claw-doctor.py --cron

# Widen or narrow the observation window (default 24h)
/opt/homebrew/bin/python3 scripts/health/claw-doctor.py --window-hours 6
```

Use `/opt/homebrew/bin/python3`. The `python3` on a bare PATH may not be the
same interpreter the crons use.

**Runtime:** ~3.5 seconds. It is cheap. Run it whenever something feels
off — that instinct was correct on 2026-10-24 and it should be trusted.

---

## The scheduled run

| Property | Value |
|----------|-------|
| Job name | `Claw Doctor` |
| Job ID | `394e32df-c65f-421d-a110-4257357c51af` |
| Schedule | Every 3 hours |
| Session target | `isolated` |
| Command timeout | 300s |
| Delivery | `announce` → telegram |
| Command | `/opt/homebrew/bin/python3 scripts/health/claw-doctor.py --cron --window-hours 6` |

### The alert policy — read this before changing it

Amre was explicit: *"you really don't need to send me Ur thoughts."* The
doctor is therefore **FAIL-first and near-silent**:

- **Healthy → prints `NO_REPLY`.** The runner suppresses it. No message.
- **FAIL → always announced**, but at most once every 6 hours while the same
  failure persists.
- **WARN → announced exactly once**, the first time it appears, and never
  again unless its status changes. A warning that is still true is not news.

The cron delivers **only the finding that woke it**, not the full
fourteen-check report. A monitoring system that dumps everything every three
hours trains its owner to ignore it, which is worse than having no monitor.

---

## What it checks, and what each verdict means

### 1. `gateway` — Gateway is alive and logging
**PASS** when `~/Library/Logs/openclaw/gateway.log` was written within the
last 30 minutes and the CLI responds.
**FAIL** when the log is stale or missing — the Gateway is down or wedged.
*Fix:* check the `ai.openclaw.gateway` launchd service.

### 2. `overflow` — Overflows are caught before the provider sees them
This is the check that would have caught the 2026-10-24 data loss.

Two things look identical in the logs but mean opposite things:

| Log line | Meaning |
|----------|---------|
| `context-overflow-diag` with `error=400:` | The request was **sent** and the provider **refused** it. The turn is lost. |
| `context-overflow-diag` with `error=Context` | The **mid-turn precheck caught it locally**. The guard did its job. |

A doctor that counted both as failures would report a healthy system as
broken. This one separates them and only fails on `400:`.

**Verdict describes the current regime, not history.** Overflows from before
the guard was enabled are history, not a live defect. It is **FAIL** only when
the most recent refusal came *after* the most recent local catch.

*Fix if failing:* compaction is running too late. Confirm `midTurnPrecheck`
is enabled and `maxActiveTranscriptBytes` trips before the wall.

### 3. `precheck` — Precheck covers every local catch
Counts precheck fires against local catches **since the last provider
refusal**. If the precheck fires but nothing is caught, the guard is not
covering the path that is failing.

*Fix:* lower `maxActiveTranscriptBytes` so the precheck trips earlier.

### 4. `truncation` — Compaction artifacts are intact
Watches for `Compaction safeguard: finalized artifact truncated`. This is
**silent content loss** — the compaction summary is cut mid-sentence and the
facts inside it vanish. This is a **separate axis from overflow**: tuning
the overflow knobs does not remove it, and the two must never be conflated.

Loss kinds seen in the wild:

| Loss kind | What was lost |
|-----------|---------------|
| `summary-tail` | The end of the compaction summary — often the most recent facts |
| `suffix-head` | The head of the transcript suffix |
| `split-turn-tail` | The tail of a partially-completed turn |
| `preserved-turn-head` | The head of a preserved turn |

Judged against the **last compaction config change**, so old losses do not
haunt a config that has since been corrected.

*Fix:* **raise** `keepRecentTokens` toward 20000. Lowering it pushes more
content into the summary, which is exactly where `summary-tail` loss happens.
If it persists, read the compaction module's summary/suffix budget split.

### 5. `compaction-config` — Compaction config is sane
Confirms `midTurnPrecheck.enabled` is true and `maxActiveTranscriptBytes` is
set. These two are the guard rails; without them, compaction happens only at
turn end, by which point the turn has already blown the context wall.

### 6. `config-drift` — Compaction knobs match the documented defaults
Compares the live config against the **documented runtime defaults** from the
`context-overflow-recovery` workshop skill:

```
keepRecentTokens   = 20000
recentTurnsPreserve = 3
```

A knob **below** the default is a warning, not a curiosity — it means more
content is being pushed into the summary where it is likelier to be
truncated. This check exists because an internal session lowered the knobs
from 12000/3 to 8000/2 at 07:37 on 2026-10-24 without asking, and the
truncation markers continued afterwards.

*Fix:* restore the documented defaults. If a change was genuinely intended,
re-baseline with `--update-baseline`.

### 7. `config-reload` — No recent config rewrites
Reports who changed the config and when, from the gateway's own reload
events. This is the forensic trail for the `config-drift` finding.

### 8. `skills` — Every skill is loadable
Walks every `SKILL.md` across all five skill roots and asserts each has
YAML frontmatter with a non-empty `description`. A skill without a
description is **invisible to the model** — it will never be loaded, and
nothing else in the system complains.

### 9. `skill-catalog` — Skill catalogue is healthy
Runs `openclaw skills check --json` and reports eligible/visible/blocked
counts plus any `missingRequirements`.

### 10. `cron-contracts` — Cron contracts hold
Asserts the jobs that carry real obligations are enabled and correctly
configured. In particular the **Friday horror book** must be:

- enabled
- `horror-book.sh --send` — without `--send` it only *recommends* a book and
  delivers nothing
- `timeoutSeconds` ≥ 300 — a Z-Library download plus an attachment upload
  does not fit in 30 seconds
- `sessionTarget: isolated`
- delivery mode `announce`

Also fails if any job has consecutive errors.

### 11. `stale-cli` — PATH openclaw matches the gateway build
**This one has bitten us twice.** The Homebrew `openclaw` on PATH is
2026.6.35; the Gateway runs 2026.9.6. The stale build **rejects the current
config as invalid**, so every config-gated command (`cron list`, `skills
list`, `config validate`) fails with a bogus "Invalid config" wall and a
`doctor --fix` prompt. It presents as a broken system when nothing is
broken.

The doctor always calls the gateway-aligned binary explicitly:

```
/Users/amre/.openclaw/tools/current-bin/openclaw
/Users/amre/.openclaw/tools/node-v24.21.0/bin/openclaw
```

Scripts should resolve `$OPENCLAW_BIN` rather than calling bare `openclaw`.

### 12. `sessions` — Session store is small
Reports the live session count and store size. A store that grows without
bound is how the transcript-deleting watchdog got triggered in the first
place.

### 13. `artifacts` — No dead artifacts on disk
Reports the 4.3GB `session-sqlite-import-archive` and the 309MB
`migration-stuck` database. **Informational only.** Deleting them is
irreversible and needs Amre's explicit yes. Disk has 3.3Ti free, so there
is no pressure to act.

### 14. `git` — Git tree is clean and published
Reports uncommitted paths and unpushed commits. `projects/drosscash` is
excluded by policy — it is deliberately left dirty.

---

## How to read a finding

```
[FAIL] Overflows are caught before the provider sees them
       the most recent overflow (2026-10-24T06:45:22Z) was REFUSED by the
       provider — 17 refusal(s) in the last 12h and the latest local catch
       is older
       - 2026-10-24T06:45:22Z REFUSED tokens=204801 session=...:telegram:direct:8125193571
       fix: compaction is running too late; check that midTurnPrecheck is
             enabled and maxActiveTranscriptBytes trips before the wall
```

Read it in this order:

1. **The verdict line** says what is broken.
2. **The detail** says how bad and how current.
3. **The evidence lines** are the raw measurements — timestamps, counts,
   sessions. They are the proof, and they are redacted: no secret ever
   appears here.
4. **The fix** says what to do. It is a direction, not an action — the
   doctor is read-only and will never change the system's configuration.

---

## Design rules this tool follows

These are not stylistic preferences. Each one was learned from a specific
failure.

1. **Read-only.** It never mutates config, sessions, git, or the filesystem.
   The only files it writes are its own state and report files under
   `~/.openclaw/state/claw-doctor/`. A diagnostic that can change the system
   is not a diagnostic.
2. **Stdlib only.** No third-party imports. It must run when everything else
   is broken — including the package manager.
3. **Resolve the CLI explicitly.** Never bare `openclaw` (see check 11).
4. **Never print secrets.** Evidence is reduced to specific fields. No whole
   log lines are echoed, because a log line can contain anything.
5. **Measure the live signal.** "Compaction truncated" is read from the log
   because that is where the symptom actually shows up — not inferred from a
   proxy such as session size.
6. **Separate the three failure modes.** Provider-refused overflow,
   locally-caught overflow, and lossy compaction have different fixes. A
   tool that lumps them together produces confident nonsense.
7. **Judge the current regime.** A verdict describes the configuration
   running now. Failures from before a relevant config change are history.
8. **A verdict needs evidence.** Every check prints the measurements that
   produced it.
9. **Silence when healthy.** The doctor earning the right to speak is what
   makes it worth listening to when it does.

---

## State and history

| File | Purpose |
|------|---------|
| `~/.openclaw/state/claw-doctor/baseline.json` | Last-seen compaction config, plus the per-check alert state used for dedupe |
| `~/.openclaw/state/claw-doctor/history.jsonl` | One line per run — counts and the overflow/truncation summary. This is the trend line. |
| `~/.openclaw/state/claw-doctor/last-report.json` | The full last report in JSON |

The history file is the raw material for a reliability *trend*. Over time it
answers "is this system getting better or worse?" rather than merely "is it
broken right now?".

Re-baselining after an intentional config change:

```bash
/opt/homebrew/bin/python3 scripts/health/claw-doctor.py --update-baseline
```

---

## Known limits — stated honestly

- **It is a point-in-time sampler.** A fault that occurs between runs and
  resolves itself may be missed. The 3-hourly cadence bounds detection
  latency, not the fault window.
- **The log window is bounded.** With `--window-hours 6` the cron only sees
  six hours of history. A fault older than that is invisible to the cron
  (the manual default of 24h sees more).
- **Log parsing is format-sensitive.** It reads the JSON log at
  `/tmp/openclaw/openclaw-YYYY-MM-DD.log` and falls back to the plain-text
  `~/Library/Logs/openclaw/gateway.log`. If OpenClaw changes its log shape,
  the checks that depend on it will silently find nothing. **If the doctor
  suddenly reports all-clear after a period of real problems, verify that it
  is still reading the log at all.**
- **It cannot see inside the compaction module.** It observes that a summary
  was truncated, not why. Explaining *why* requires reading the module's
  budget split.
- **It does not test the skills' behaviour.** It verifies that skills are
  loadable and described, not that they work.

---

## Related

- `~/.openclaw/agents/main/agent/workshop-skills/context-overflow-recovery/SKILL.md`
  — the authoritative guide to the overflow and truncation axes. The
  `context-overflow-recovery` skill is where the documented defaults and the
  correct fix directions come from.
- `../cron-health-check.py` — the narrower cron-only checker.
- `../publish-gate.sh` — the credential gate that runs on every push.
- `HEARTBEAT.md` — the periodic-check protocol.
- `memory/2026-10-24.md` — the full findings from the day this was built.

---

*Built 2026-10-24, in response to "We need a way or a system to check this
reliability. A py script or something like our own claw doctor."*
