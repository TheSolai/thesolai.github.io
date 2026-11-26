#!/usr/bin/env python3
"""
Post-process a mirrored site:
  1. Decode Cloudflare email-protection obfuscation into plain mailto: links.
  2. Rewrite root-absolute /cdn-cgi/... script paths to relative local paths.
  3. Strip cache-busting ?v=... from local refs (harmless, cleaner).
"""
import os
import re
import sys

CF_ENC = re.compile(
    r'<a\b[^>]*class="[^"]*__cf_email__[^"]*"[^>]*data-cfemail="([0-9a-fA-F]+)"[^>]*>(.*?)</a>',
    re.S | re.I,
)
CF_HREF = re.compile(r'/cdn-cgi/l/email-protection#([0-9a-fA-F]+)')
CF_SPAN = re.compile(
    r'<span\b[^>]*class="[^"]*__cf_email__[^"]*"[^>]*data-cfemail="([0-9a-fA-F]+)"[^>]*>(.*?)</span>',
    re.S | re.I,
)


def cf_decode(hexstr):
    """Cloudflare email protection: first byte is XOR key for the rest."""
    h = hexstr.strip()
    if len(h) < 4:
        return ""
    try:
        key = int(h[0:2], 16)
        out = []
        for i in range(2, len(h), 2):
            out.append(int(h[i:i + 2], 16) ^ key)
        return bytes(out).decode("utf-8", "replace")
    except Exception:
        return ""


def main():
    root = os.path.abspath(sys.argv[1])
    touched = 0
    for dirpath, _dirs, files in os.walk(root):
        for fn in files:
            if not fn.endswith(".html"):
                continue
            fp = os.path.join(dirpath, fn)
            txt = open(fp, encoding="utf-8", errors="replace").read()
            orig = txt

            # 1. <a class="__cf_email__" data-cfemail="..">text</a> -> real mailto
            def fix_a(m):
                mail = cf_decode(m.group(1))
                if not mail or "@" not in mail:
                    return m.group(0)
                return f'<a href="mailto:{mail}">{mail}</a>'

            txt = CF_ENC.sub(fix_a, txt)

            # 2. <span class="__cf_email__" data-cfemail="..">text</span> -> text
            def fix_span(m):
                mail = cf_decode(m.group(1))
                return mail if "@" in mail else m.group(0)

            txt = CF_SPAN.sub(fix_span, txt)

            # 3. any leftover /cdn-cgi/l/email-protection#<hex> hrefs
            def fix_href(m):
                mail = cf_decode(m.group(1))
                return f"mailto:{mail}" if "@" in mail else m.group(0)

            txt = CF_HREF.sub(fix_href, txt)

            # 4. root-absolute cdn-cgi script -> relative (pages live at root)
            txt = txt.replace('src="/cdn-cgi/', 'src="cdn-cgi/')
            txt = txt.replace('href="/cdn-cgi/', 'href="cdn-cgi/')

            # 5. strip cache-busting query from local refs
            def strip_q(m):
                q = m.group(2)
                if q and re.match(r'^v=\d+', q):
                    return m.group(1)
                return m.group(0)

            txt = re.sub(r'((?:href|src)="([^"?#]+))\?v=\d+', strip_q, txt)

            if txt != orig:
                open(fp, "w", encoding="utf-8").write(txt)
                touched += 1

    print(f"patched_files={touched}")


if __name__ == "__main__":
    main()
