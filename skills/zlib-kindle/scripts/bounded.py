#!/usr/bin/env python3
"""Bounded output capture for the delivery jobs that announce to a chat.

The daily Z-Library runs are announced to Telegram. The scripts they call
print per-file progress, and the shared zlib_kindle helpers print their own
verification lines -- so a long backlog, a file that fails an OPF check, or
a search that returns a lot could turn one run into a flood.

Every line the job produces is captured here, under both a line count and a
character count, and the verdict is always printed last, so the outcome of a
run is never lost to truncation. The full uncapped output can still be
written to a log file, so nothing is lost for auditing -- it just never
reaches the chat.
"""

import sys

# Both a line count and a character count apply. The character count alone
# would let one enormous line through; the line count alone would let many
# short ones through.
MAX_LINES = 40
MAX_CHARS = 3000

# Room kept free at the end of the character budget so the verdict is always
# printed in full, even when the body used every character it was given.
VERDICT_RESERVE = 400


class Bounded:
    """Capture stdout and stderr under a line and character cap."""

    encoding = "utf-8"
    errors = "replace"

    def __init__(self, max_lines=MAX_LINES, max_chars=MAX_CHARS,
                 reserve=VERDICT_RESERVE, log_path=None):
        self.max_lines = max_lines
        self.max_chars = max_chars
        self.reserve = reserve
        self.log_path = log_path
        self.lines = []
        self.chars = 0
        self.dropped = 0
        self._out = None
        self._err = None
        self._log = None

    def write(self, text):
        if not text:
            return 0
        if self._log is not None:
            try:
                self._log.write(text)
            except OSError:
                pass
        for line in text.splitlines(keepends=True):
            if len(self.lines) >= self.max_lines:
                self.dropped += 1
                continue
            if self.chars + len(line) > self.max_chars - self.reserve:
                self.dropped += 1
                continue
            self.lines.append(line)
            self.chars += len(line)
        return len(text)

    def flush(self):
        pass

    def isatty(self):
        return False

    def __enter__(self):
        self._out, self._err = sys.stdout, sys.stderr
        sys.stdout = self
        sys.stderr = self
        if self.log_path:
            try:
                self._log = open(self.log_path, "a", encoding="utf-8")
            except OSError:
                self._log = None
        return self

    def __exit__(self, *exc):
        sys.stdout, sys.stderr = self._out, self._err
        if self._log is not None:
            try:
                self._log.close()
            except OSError:
                pass
            self._log = None
        return False

    def emit(self, verdict):
        """Write the captured output, then the verdict, to real stdout."""
        for line in self.lines:
            self._out.write(line)
        if self.dropped:
            self._out.write("  ... %d more line(s) not shown\n" % self.dropped)
        if verdict:
            self._out.write(str(verdict).rstrip("\n") + "\n")
        self._out.flush()
