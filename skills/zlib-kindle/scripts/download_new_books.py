#!/usr/bin/env python3
"""Download the new themed books from Project Gutenberg and verify each one.

Gutenberg is used because the Z-Library daily download cap is already
exhausted, and because every book here is public domain and comes with a
stable EPUB. Nothing is trusted on filename alone: the file's own title and
author are read back out of its metadata and checked against what was
requested, so a mis-titled or mis-mapped download can never be merged or
sent.
"""

import os
import sys
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import zlib_kindle as zk  # noqa: E402

LIB = os.path.expanduser("~/Downloads/dross-books")
os.makedirs(LIB, exist_ok=True)

# filename -> (gutenberg id, title fragments accepted in file metadata,
#               author fragment that must appear in the file metadata)
BOOKS = {
    # --- heaven and hell ---
    "Marriage-of-Heaven-and-Hell-Blake.epub": (45315, ("marriage of heaven",), "blake"),
    "Hound-of-Heaven-Thompson.epub": (30730, ("hound of heaven",), "thompson"),
    "The-Inferno-Dante-Dore.epub": (8789, ("vision of hell", "inferno"), "dante"),
    "The-Possessed-Dostoevsky.epub": (8117, ("possessed", "devils"), "dostoyevsky"),
    "Sorrows-of-Satan-Corelli.epub": (42332, ("sorrows of satan",), "corelli"),
    "Great-Controversy-Christ-and-Satan.epub": (25833, ("great controversy",), None),
    "Devil-Stories-Anthology.epub": (31754, ("devil stories",), None),
    "The-Angel-and-the-Demon.epub": (67996, ("angel and the demon",), None),
    "Seraphita-Balzac.epub": (1432, ("seraphita",), "balzac"),
    "Heaven-and-Its-Wonders-and-Hell.epub": (17368, ("heaven and its wonders",), None),
    "Daemonologie-James-VI.epub": (25929, ("daemonologie",), None),
    "Devil-Worship-in-France.epub": (21258, ("devil-worship", "devil worship"), None),
    "Story-of-the-Heavens-Jeans.epub": (27378, ("story of the heavens",), None),

    # --- the complete Oz series ---
    "Oz-01-Wonderful-Wizard.epub": (55, ("wonderful wizard",), "baum"),
    "Oz-02-Marvelous-Land.epub": (54, ("marvelous land",), "baum"),
    "Oz-03-Ozma-of-Oz.epub": (486, ("ozma of oz",), "baum"),
    "Oz-04-Dorothy-and-the-Wizard.epub": (22566, ("dorothy and the wizard",), "baum"),
    "Oz-05-Road-to-Oz.epub": (26624, ("road to oz",), "baum"),
    "Oz-06-Emerald-City-of-Oz.epub": (517, ("emerald city",), "baum"),
    "Oz-07-Lost-Princess-of-Oz.epub": (959, ("lost princess",), "baum"),
    "Oz-08-Tik-Tok-of-Oz.epub": (956, ("tik-tok", "tik tok"), "baum"),
    "Oz-09-Rinkitink-in-Oz.epub": (25581, ("rinkitink",), "baum"),
    "Oz-10-Magic-of-Oz.epub": (419, ("magic of oz",), "baum"),
    "Oz-11-Tin-Woodman-of-Oz.epub": (960, ("tin woodman", "tin forest"), "baum"),
    "Oz-12-Patchwork-Girl-of-Oz.epub": (32094, ("patchwork girl",), "baum"),

    # --- the complete Barsoom (John Carter) series ---
    "Mars-01-Princess-of-Mars.epub": (62, ("princess of mars",), "burroughs"),
    "Mars-02-Gods-of-Mars.epub": (64, ("gods of mars",), "burroughs"),
    "Mars-03-Warlord-of-Mars.epub": (68, ("warlord of mars",), "burroughs"),
    "Mars-04-Thuvia-Maid-of-Mars.epub": (72, ("thuvia",), "burroughs"),
    "Mars-05-Chessmen-of-Mars.epub": (1153, ("chessmen of mars",), "burroughs"),
    "Mars-06-Master-Mind-of-Mars.epub": (69703, ("master mind", "master mind of mars"), "burroughs"),

    # --- the complete Poe ---
    "Poe-Works-Vol-1.epub": (2147, ("works of edgar allan poe",), "poe"),
    "Poe-Works-Vol-2.epub": (2148, ("works of edgar allan poe",), "poe"),
    "Poe-Works-Vol-3.epub": (2149, ("works of edgar allan poe",), "poe"),
    "Poe-Works-Vol-4.epub": (2150, ("works of edgar allan poe",), "poe"),
    "Poe-Works-Vol-5.epub": (2151, ("works of edgar allan poe",), "poe"),

    # --- complete single-author collections ---
    "Bierce-Collected-Works-Vol-1.epub": (13541, ("collected works of ambrose bierce",), "bierce"),
    "Bierce-Collected-Works-Vol-2.epub": (13334, ("collected works of ambrose bierce",), "bierce"),
    "The-Three-Impostors-Machen.epub": (35517, ("three impostors",), "machen"),
    "Dunsany-Gods-of-Pegana.epub": (8395, ("gods of pegana",), "dunsany"),
    "Dunsany-Book-of-Wonder.epub": (7477, ("book of wonder",), "dunsany"),
    "Dunsany-Time-and-the-Gods.epub": (8183, ("time and the gods",), "dunsany"),
    "Dunsany-Sword-of-Welleran.epub": (10806, ("sword of welleran",), "dunsany"),
    "Dunsany-Fifty-One-Tales.epub": (7838, ("fifty-one tales",), "dunsany"),
    "Dunsany-A-Dreamers-Tales.epub": (8129, ("dreamer's tales", "dreamers tales"), "dunsany"),
}


def verify(path, want_titles, want_author):
    """Confirm the file really is the book that was asked for."""
    title, creator = zk.epub_metadata(path)
    if not title:
        return False, "no title metadata inside the file"
    low = title.lower()
    if not any(w in low for w in want_titles):
        return False, f"internal title {title!r} is not one of {want_titles}"
    if want_author:
        if not creator:
            return False, "no author metadata inside the file"
        if want_author not in creator.lower():
            return False, f"internal author {creator!r} lacks {want_author!r}"
    ok, fmt = zk.preflight_book(path)
    if not ok:
        return False, f"preflight failed: {fmt}"
    return True, f"{title} / {creator}"


def main():
    only = sys.argv[1:]
    results = []
    for filename, (gid, want_titles, want_author) in BOOKS.items():
        if only and not any(o in filename for o in only):
            continue
        path = os.path.join(LIB, filename)
        if os.path.isfile(path):
            ok, detail = verify(path, want_titles, want_author)
            if ok:
                print(f"  = {filename}: already present and verified")
                results.append((filename, True, detail))
                continue
            print(f"  ~ {filename}: present but unverifiable ({detail}); refetching")
            os.remove(path)

        if not zk.gutenberg_fetch(gid, path):
            print(f"  ! {filename}: download failed (gutenberg id {gid})")
            results.append((filename, False, "download failed"))
            continue

        ok, detail = verify(path, want_titles, want_author)
        if not ok:
            print(f"  ! {filename}: REJECTED ({detail})")
            results.append((filename, False, detail))
            continue

        size = os.path.getsize(path)
        print(f"  ✓ {filename}  ({size:,} bytes)  {detail}")
        results.append((filename, True, f"{size} bytes"))

    good = sum(1 for _, ok, _ in results if ok)
    print(f"\n=== {good}/{len(results)} books downloaded and verified ===")
    with open("/tmp/drossprobe/new-books.json", "w") as fh:
        json.dump([{"file": f, "ok": ok, "detail": d} for f, ok, d in results],
                  fh, indent=1)
    return 0 if good == len(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
