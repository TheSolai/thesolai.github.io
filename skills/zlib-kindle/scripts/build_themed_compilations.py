#!/usr/bin/env python3
"""Build the heaven/hell/angel/devil compilations and verify each one.

Every volume is a Gutenberg EPUB (no Z-Library daily cap), each source file
is checked against the title/author it was requested under *before* it goes
into a compilation, and each merged compilation is re-checked afterwards so
a bad merge can never reach the Kindle address.
"""

import os
import sys
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import epub_merge  # noqa: E402
import zlib_kindle as zk  # noqa: E402

LIB = os.path.expanduser("~/Downloads/dross-books")
OUT = os.path.join(LIB, "compilations")
os.makedirs(OUT, exist_ok=True)

# filename -> (title fragments accepted in the file's own metadata,
#               author fragment, content marker that must appear in the text)
# Gutenberg titles the Longfellow Dante volumes by section name ("Hell",
# "Purgatory", "Paradise"), so the title check accepts either naming and the
# content marker settles which part of the Comedy the file really is.
SOURCES = {
    "Divine-Comedy-1-Inferno-Longfellow.epub": (("hell", "inferno"), "dante", "INFERNO"),
    "Divine-Comedy-2-Purgatorio-Longfellow.epub": (("purgatory", "purgatorio"), "dante", "PURGATORIO"),
    "Divine-Comedy-3-Paradiso-Longfellow.epub": (("paradise", "paradiso"), "dante", "PARADISO"),
    "Paradise-Lost-Milton.epub": (("paradise lost",), "milton", None),
    "Paradise-Regained-Milton.epub": (("paradise regained",), "milton", None),
    "The-City-of-God-Vol-1-Augustine.epub": (("city of god",), "augustine", None),
    "The-City-of-God-Vol-2-Augustine.epub": (("city of god",), "augustine", None),
    "The-Devils-Dictionary-Bierce.epub": (("devil's dictionary",), "bierce", None),
    "Demonology-and-Devil-lore.epub": (("demonology",), "conway", None),
    "The-Discoverie-of-Witchcraft-Scot.epub": (("discoverie of witchcraft",), "scot", None),
    "The-Book-of-Enoch.epub": (("enoch",), None, None),
    "The-Revelation-of-Saint-John.epub": (("revelation",), None, None),
    "The-Great-God-Pan-by-Arthur-Machen.epub": (("great god pan",), "machen", None),
    "The-King-in-Yellow-Chambers.epub": (("king in yellow",), "chambers", None),
    "The-House-on-the-Borderland-Hodgson.epub": (("house on the borderland",), "hodgson", None),
    "Doctor-Faustus-Marlowe.epub": (("faustus",), "marlowe", None),
    "Faust-Part-1-Goethe.epub": (("faust",), "goethe", None),
    "The-Pilgrims-Progress-Bunyan.epub": (("pilgrim",), "bunyan", None),
    "A-Christmas-Carol-Dickens.epub": (("christmas carol",), "dickens", None),
}

# (output name, title, author, [(source filename, volume title), ...])
COMPILATIONS = [
    ("The-Divine-Comedy-Dante.epub",
     "The Divine Comedy",
     "Dante Alighieri",
     [("Divine-Comedy-1-Inferno-Longfellow.epub", "Inferno, Part I of the Divine Comedy"),
      ("Divine-Comedy-2-Purgatorio-Longfellow.epub", "Purgatorio, Part II of the Divine Comedy"),
      ("Divine-Comedy-3-Paradiso-Longfellow.epub", "Paradiso, Part III of the Divine Comedy")]),

    ("Paradise-Lost-and-Paradise-Regained-Milton.epub",
     "Paradise Lost and Paradise Regained",
     "John Milton",
     [("Paradise-Lost-Milton.epub", "Paradise Lost"),
      ("Paradise-Regained-Milton.epub", "Paradise Regained")]),

    ("The-City-of-God-Augustine.epub",
     "The City of God",
     "Saint Augustine of Hippo",
     [("The-City-of-God-Vol-1-Augustine.epub", "The City of God, Volume I"),
      ("The-City-of-God-Vol-2-Augustine.epub", "The City of God, Volume II")]),

    ("The-Devils-Library-Bierce-Scot-Conway.epub",
     "The Devil's Library",
     "Ambrose Bierce, Reginald Scot and Moncure Daniel Conway",
     [("The-Devils-Dictionary-Bierce.epub", "The Devil's Dictionary by Ambrose Bierce"),
      ("Demonology-and-Devil-lore.epub", "Demonology and Devil-lore by Moncure Daniel Conway"),
      ("The-Discoverie-of-Witchcraft-Scot.epub",
       "The Discoverie of Witchcraft by Reginald Scot")]),

    ("The-Watched-Wood-Three-Panics.epub",
     "The Watched Wood: Three Narratives of the Old Gods",
     "Arthur Machen, Robert W. Chambers and William Hope Hodgson",
     [("The-Great-God-Pan-by-Arthur-Machen.epub", "The Great God Pan by Arthur Machen"),
      ("The-King-in-Yellow-Chambers.epub", "The King in Yellow by Robert W. Chambers"),
      ("The-House-on-the-Borderland-Hodgson.epub",
       "The House on the Borderland by William Hope Hodgson")]),

    ("Apocalypse-The-Book-of-Enoch-and-Revelation.epub",
     "Apocalypse: The Book of Enoch and The Revelation of Saint John",
     "Anonymous",
     [("The-Book-of-Enoch.epub", "The Book of Enoch"),
      ("The-Revelation-of-Saint-John.epub", "The Revelation of Saint John")]),

    ("Fausts-Bargain-Marlowe-and-Goethe.epub",
     "Faust's Bargain: Doctor Faustus and Faust",
     "Christopher Marlowe and Johann Wolfgang von Goethe",
     [("Doctor-Faustus-Marlowe.epub",
       "The Tragical History of Doctor Faustus by Christopher Marlowe"),
      ("Faust-Part-1-Goethe.epub", "Faust, Part One by Johann Wolfgang von Goethe")]),

    ("The-Journey-to-the-Celestial-City.epub",
     "The Journey to the Celestial City",
     "John Bunyan and Charles Dickens",
     [("The-Pilgrims-Progress-Bunyan.epub", "The Pilgrim's Progress by John Bunyan"),
      ("A-Christmas-Carol-Dickens.epub", "A Christmas Carol by Charles Dickens")]),
]


def check_source(filename):
    """Confirm the source file really is the book it claims to be."""
    path = os.path.join(LIB, filename)
    if not os.path.isfile(path):
        return False, f"missing source file {filename}"
    want_titles, want_author, marker = SOURCES[filename]
    title, creator = zk.epub_metadata(path)
    if not title:
        return False, f"{filename}: no title metadata inside the file"
    low = title.lower()
    if not any(w in low for w in want_titles):
        return False, f"{filename}: internal title {title!r} is not one of {want_titles}"
    if want_author:
        if not creator:
            return False, f"{filename}: no author metadata inside the file"
        if want_author not in creator.lower():
            return False, f"{filename}: internal author {creator!r} lacks {want_author!r}"
    if marker:
        body = zk._epub_text(path, 200_000).upper()
        if marker not in body:
            return False, f"{filename}: content marker {marker!r} absent from the text"
    ok, fmt = zk.preflight_book(path)
    if not ok:
        return False, f"{filename}: preflight failed: {fmt}"
    return True, f"{title} / {creator}"


def main():
    results = []
    for out_name, title, author, volumes in COMPILATIONS:
        # 1. verify every source volume
        bad = False
        for filename, _vol_title in volumes:
            ok, detail = check_source(filename)
            if not ok:
                print(f"  ! REJECT {detail}")
                bad = True
                break
        if bad:
            results.append((out_name, False, "source rejected"))
            continue

        # 2. merge
        entries = [(os.path.join(LIB, f), vol_title) for f, vol_title in volumes]
        out_path = os.path.join(OUT, out_name)
        epub_merge.merge(entries, out_path, title, author)

        # 3. verify the merged file
        got_title, got_creator = zk.epub_metadata(out_path)
        problems = []
        if not got_title or got_title != title:
            problems.append(f"merged title is {got_title!r}, wanted {title!r}")
        if not got_creator:
            problems.append("merged file states no author")
        ok, fmt = zk.preflight_book(out_path)
        if not ok:
            problems.append(f"preflight failed: {fmt}")
        if not zk.epub_namespace_ok(out_path):
            problems.append("merged OPF does not use the default namespace")
        size = os.path.getsize(out_path)
        if size == 0:
            problems.append("merged file is empty")

        if problems:
            for p in problems:
                print(f"  ! {out_name}: {p}")
            results.append((out_name, False, "; ".join(problems)))
            continue

        print(f"  ✓ {out_name}  ({size:,} bytes, {len(volumes)} volumes)")
        results.append((out_name, True, f"{size} bytes"))

    print("\n=== built {0}/{1} compilations ===".format(
        sum(1 for _, ok, _ in results if ok), len(results)))
    with open("/tmp/drossprobe/compilation-build.json", "w") as fh:
        json.dump([{"file": f, "ok": ok, "detail": d} for f, ok, d in results], fh, indent=1)
    return 0 if all(ok for _, ok, _ in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
