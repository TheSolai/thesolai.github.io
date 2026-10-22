#!/usr/bin/env python3
"""
Importable shim for `blog-cron-v2.py`.

WHY: the "Sol — Blog Post" cron payload runs:
    import blog_cron_v2 as m; m.main()
but the implementation file is named `blog-cron-v2.py` (hyphens).
Hyphens are not valid Python identifiers, so the import raised
ModuleNotFoundError and the cron exited with code 2 on every run —
6 consecutive failures and counting.

This shim loads the real module by path (importlib) so the cron can import
it under the underscore name it actually asks for.

Run directly to invoke the same code path:
    python3 blog_cron_v2.py
"""

import importlib.util
import os
import sys

_REAL = os.path.join(os.path.dirname(os.path.abspath(__file__)), "blog-cron-v2.py")

_spec = importlib.util.spec_from_file_location("blog_cron_v2_impl", _REAL)
if _spec is None or _spec.loader is None:
    raise ImportError(f"Could not load blog cron implementation from {_REAL}")

_mod = importlib.util.module_from_spec(_spec)
sys.modules["blog_cron_v2_impl"] = _mod
_spec.loader.exec_module(_mod)

# Re-export the public surface the cron payload uses.
main = _mod.main
commit_and_push = _mod.commit_and_push
log = _mod.log

if __name__ == "__main__":
    main()
