#!/usr/bin/env python3
"""Build the angel/demon/devil/heaven/hell compilations and the complete
series compilations, then verify every one of them.

Every source file is checked against the title and author it was requested
under *before* it goes into a compilation, and every merged compilation is
re-checked afterwards, so a bad merge can never reach the Kindle address.
A merged file that is still too big for the mail API is slimmed and
re-verified before it is accepted.
"""

import os
import sys
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import epub_merge  # noqa: E402
import zlib_kindle as zk  # noqa: E402
import slim_epub  # noqa: E402

LIB = os.path.expanduser("~/Downloads/dross-books")
OUT = os.path.join(LIB, "compilations")
os.makedirs(OUT, exist_ok=True)

# The mail API rejects an oversized attachment with a 413. 4,130,844 bytes
# was accepted and 6,757,855 bytes was refused, so the ceiling is somewhere
# in between. Stay well under the lower of those two.
#
# This must stay at or below the delivery script's MAX_ATTACHMENT_BYTES, or a
# compilation could be built that the mail API would then refuse.
MAX_MERGED_BYTES = 3_400_000

# Applied to a merged file that is still over the ceiling. Each pass is
# progressively more aggressive.
SLIM_PASSES = [
    {"threshold": 4_000, "max_edge": 420, "quality": 20, "colors": 16},
    {"threshold": 1, "max_edge": 320, "quality": 15, "colors": 8},
    {"threshold": 1, "max_edge": 240, "quality": 12, "colors": 4},
]

# filename -> (accepted internal title fragments, author fragment or None)
SOURCES = {
    # angels
    "Seraphita-Balzac.epub": (("seraphita",), "balzac"),
    "The-Angel-and-the-Demon.epub": (("angel and the demon",), "arthur"),
    "Hound-of-Heaven-Thompson.epub": (("hound of heaven",), "thompson"),
    # demons
    "The-Possessed-Dostoevsky.epub": (("possessed",), "dostoyevsky"),
    "The-Three-Impostors-Machen.epub": (("three impostors",), "machen"),
    "Devil-Stories-Anthology.epub": (("devil stories",), None),
    # devils
    "Daemonologie-James-VI.epub": (("daemonologie",), "james"),
    "Devil-Worship-in-France.epub": (("devil-worship in france",
                                       "devil worship in france"), "waite"),
    "Sorrows-of-Satan-Corelli.epub": (("sorrows of satan",), "corelli"),
    # heaven and hell
    "Heaven-and-Its-Wonders-and-Hell.epub": (("heaven and its wonders",),
                                               "swedenborg"),
    "Marriage-of-Heaven-and-Hell-Blake.epub": (("marriage of heaven and hell",),
                                               "blake"),
    "Story-of-the-Heavens-Jeans.epub": (("story of the heavens",), "ball"),
    "Great-Controversy-Christ-and-Satan.epub": (("great controversy",), "white"),
    "The-Inferno-Dante-Dore.epub": (("vision of hell", "inferno"), "dante"),
    # series
    "Oz-01-Wonderful-Wizard.epub": (("wizard of oz",), "baum"),
    "Oz-02-Marvelous-Land.epub": (("marvelous land of oz",), "baum"),
    "Oz-03-Ozma-of-Oz.epub": (("ozma of oz",), "baum"),
    "Oz-04-Dorothy-and-the-Wizard.epub": (("dorothy and the wizard",), "baum"),
    "Oz-05-Road-to-Oz.epub": (("road to oz",), "baum"),
    "Oz-06-Emerald-City-of-Oz.epub": (("emerald city of oz",), "baum"),
    "Oz-07-Lost-Princess-of-Oz.epub": (("lost princess of oz",), "baum"),
    "Oz-08-Tik-Tok-of-Oz.epub": (("tik-tok of oz",), "baum"),
    "Oz-09-Rinkitink-in-Oz.epub": (("rinkitink in oz",), "baum"),
    "Oz-10-Magic-of-Oz.epub": (("magic of oz",), "baum"),
    "Oz-11-Tin-Woodman-of-Oz.epub": (("tin woodman of oz",), "baum"),
    "Oz-12-Patchwork-Girl-of-Oz.epub": (("patchwork girl of oz",), "baum"),
    "Mars-01-Princess-of-Mars.epub": (("princess of mars",), "burroughs"),
    "Mars-02-Gods-of-Mars.epub": (("gods of mars",), "burroughs"),
    "Mars-03-Warlord-of-Mars.epub": (("warlord of mars",), "burroughs"),
    "Mars-04-Thuvia-Maid-of-Mars.epub": (("thuvia",), "burroughs"),
    "Mars-05-Chessmen-of-Mars.epub": (("chessmen of mars",), "burroughs"),
    "Mars-06-Master-Mind-of-Mars.epub": (("master mind of mars",), "burroughs"),
    "Poe-Works-Vol-1.epub": (("works of edgar allan poe",), "poe"),
    "Poe-Works-Vol-2.epub": (("works of edgar allan poe",), "poe"),
    "Poe-Works-Vol-3.epub": (("works of edgar allan poe",), "poe"),
    "Poe-Works-Vol-4.epub": (("works of edgar allan poe",), "poe"),
    "Poe-Works-Vol-5.epub": (("works of edgar allan poe",), "poe"),
    "Bierce-Collected-Works-Vol-1.epub": (("collected works of ambrose bierce",),
                                          "bierce"),
    "Bierce-Collected-Works-Vol-2.epub": (("collected works of ambrose bierce",),
                                          "bierce"),
    "Dunsany-A-Dreamers-Tales.epub": (("dreamer's tales",), "dunsany"),
    "Dunsany-Book-of-Wonder.epub": (("book of wonder",), "dunsany"),
    "Dunsany-Fifty-One-Tales.epub": (("fifty-one tales",), "dunsany"),
    "Dunsany-Gods-of-Pegana.epub": (("gods of pegana",), "dunsany"),
    "Dunsany-Sword-of-Welleran.epub": (("sword of welleran",), "dunsany"),
    "Dunsany-Time-and-the-Gods.epub": (("time and the gods",), "dunsany"),
}

# (output name, title, author, [(source filename, volume title), ...])
COMPILATIONS = [
    # --- angels, demons, devils, heaven, hell -------------------------
    ("Angels-and-Seraphim.epub",
     "Angels and Seraphim",
     "Honore de Balzac, T. S. Arthur and Francis Thompson",
     [("Seraphita-Balzac.epub", "Seraphita by Honore de Balzac"),
      ("The-Angel-and-the-Demon.epub",
       "The Angel and the Demon by T. S. Arthur"),
      ("Hound-of-Heaven-Thompson.epub",
       "The Hound of Heaven by Francis Thompson")]),

    ("The-Hosts-of-Darkness.epub",
     "The Hosts of Darkness",
     "Fyodor Dostoyevsky, Arthur Machen and Ambrose Bierce",
     [("The-Possessed-Dostoevsky.epub", "The Possessed by Fyodor Dostoyevsky"),
      ("The-Three-Impostors-Machen.epub", "The Three Impostors by Arthur Machen"),
      ("Devil-Stories-Anthology.epub", "Devil Stories: An Anthology")]),

    ("The-Devils-Court.epub",
     "The Devil's Court",
     "James VI of Scotland, Arthur Edward Waite and Marie Corelli",
     [("Daemonologie-James-VI.epub", "Daemonologie by King James VI"),
      ("Devil-Worship-in-France.epub",
       "Devil-Worship in France by Arthur Edward Waite"),
      ("Sorrows-of-Satan-Corelli.epub", "The Sorrows of Satan by Marie Corelli")]),

    ("Heaven-and-Its-Wonders.epub",
     "Heaven and Its Wonders",
     "Emanuel Swedenborg, William Blake and Robert S. Ball",
     [("Heaven-and-Its-Wonders-and-Hell.epub",
       "Heaven and Its Wonders and Hell by Emanuel Swedenborg"),
      ("Marriage-of-Heaven-and-Hell-Blake.epub",
       "The Marriage of Heaven and Hell by William Blake"),
      ("Story-of-the-Heavens-Jeans.epub",
       "The Story of the Heavens by Robert S. Ball")]),

    ("The-Vision-of-Hell.epub",
     "The Vision of Hell: Dante and the Great Controversy",
     "Dante Alighieri and Ellen G. White",
     [("The-Inferno-Dante-Dore.epub",
       "The Vision of Hell by Dante Alighieri, illustrated by Gustave Dore"),
      ("Great-Controversy-Christ-and-Satan.epub",
       "The Great Controversy Between Christ and Satan by Ellen G. White")]),

    # --- complete series ----------------------------------------------
    ("The-Oz-Series-Part-I-Books-1-to-6.epub",
     "The Oz Series, Part I: Books One to Six",
     "L. Frank Baum",
     [("Oz-01-Wonderful-Wizard.epub", "The Wonderful Wizard of Oz"),
      ("Oz-02-Marvelous-Land.epub", "The Marvelous Land of Oz"),
      ("Oz-03-Ozma-of-Oz.epub", "Ozma of Oz"),
      ("Oz-04-Dorothy-and-the-Wizard.epub", "Dorothy and the Wizard in Oz"),
      ("Oz-05-Road-to-Oz.epub", "The Road to Oz"),
      ("Oz-06-Emerald-City-of-Oz.epub", "The Emerald City of Oz")]),

    ("The-Oz-Series-Part-II-Books-7-to-12.epub",
     "The Oz Series, Part II: Books Seven to Twelve",
     "L. Frank Baum",
     [("Oz-07-Lost-Princess-of-Oz.epub", "The Lost Princess of Oz"),
      ("Oz-08-Tik-Tok-of-Oz.epub", "Tik-Tok of Oz"),
      ("Oz-09-Rinkitink-in-Oz.epub", "Rinkitink in Oz"),
      ("Oz-10-Magic-of-Oz.epub", "The Magic of Oz"),
      ("Oz-11-Tin-Woodman-of-Oz.epub", "The Tin Woodman of Oz"),
      ("Oz-12-Patchwork-Girl-of-Oz.epub", "The Patchwork Girl of Oz")]),

    ("The-Barsoom-Chronicles.epub",
     "The Barsoom Chronicles",
     "Edgar Rice Burroughs",
     [("Mars-01-Princess-of-Mars.epub", "A Princess of Mars"),
      ("Mars-02-Gods-of-Mars.epub", "The Gods of Mars"),
      ("Mars-03-Warlord-of-Mars.epub", "The Warlord of Mars"),
      ("Mars-04-Thuvia-Maid-of-Mars.epub", "Thuvia, Maid of Mars"),
      ("Mars-05-Chessmen-of-Mars.epub", "The Chessmen of Mars"),
      ("Mars-06-Master-Mind-of-Mars.epub", "The Master Mind of Mars")]),

    ("The-Works-of-Edgar-Allan-Poe-Complete.epub",
     "The Works of Edgar Allan Poe, Complete in Five Volumes",
     "Edgar Allan Poe",
     [("Poe-Works-Vol-1.epub", "The Works of Edgar Allan Poe, Volume 1"),
      ("Poe-Works-Vol-2.epub", "The Works of Edgar Allan Poe, Volume 2"),
      ("Poe-Works-Vol-3.epub", "The Works of Edgar Allan Poe, Volume 3"),
      ("Poe-Works-Vol-4.epub", "The Works of Edgar Allan Poe, Volume 4"),
      ("Poe-Works-Vol-5.epub", "The Works of Edgar Allan Poe, Volume 5")]),

    ("The-Collected-Works-of-Ambrose-Bierce.epub",
     "The Collected Works of Ambrose Bierce, Volumes One and Two",
     "Ambrose Bierce",
     [("Bierce-Collected-Works-Vol-1.epub",
       "The Collected Works of Ambrose Bierce, Volume 1"),
      ("Bierce-Collected-Works-Vol-2.epub",
       "The Collected Works of Ambrose Bierce, Volume 2")]),

    ("The-Fantasy-Tales-of-Lord-Dunsany.epub",
     "The Fantasy Tales of Lord Dunsany",
     "Lord Dunsany",
     [("Dunsany-A-Dreamers-Tales.epub", "A Dreamer's Tales"),
      ("Dunsany-Book-of-Wonder.epub", "The Book of Wonder"),
      ("Dunsany-Fifty-One-Tales.epub", "Fifty-One Tales"),
      ("Dunsany-Gods-of-Pegana.epub", "The Gods of Pegana"),
      ("Dunsany-Sword-of-Welleran.epub", "The Sword of Welleran"),
      ("Dunsany-Time-and-the-Gods.epub", "Time and the Gods")]),
]


def check_source(filename):
    """Confirm the source file really is the book it claims to be."""
    path = os.path.join(LIB, filename)
    if not os.path.isfile(path):
        return False, f"missing source file {filename}"
    want_titles, want_author = SOURCES[filename]
    title, creator = zk.epub_metadata(path)
    if not title:
        return False, f"{filename}: no title metadata inside the file"
    low = title.lower()
    if not any(w in low for w in want_titles):
        return False, (f"{filename}: internal title {title!r} "
                       f"is not one of {want_titles}")
    if want_author:
        if not creator:
            return False, f"{filename}: no author metadata inside the file"
        if want_author not in creator.lower():
            return False, (f"{filename}: internal author {creator!r} "
                           f"lacks {want_author!r}")
    ok, fmt = zk.preflight_book(path)
    if not ok:
        return False, f"{filename}: preflight failed: {fmt}"
    return True, f"{title} / {creator}"


def verify_merged(path, title, author):
    """Return a list of problems with a merged compilation."""
    problems = []
    got_title, got_creator = zk.epub_metadata(path)
    if not got_title or got_title != title:
        problems.append(f"merged title is {got_title!r}, wanted {title!r}")
    if not got_creator:
        problems.append("merged file states no author")
    if author and got_creator and author.lower() != got_creator.lower():
        problems.append(f"merged author is {got_creator!r}, wanted {author!r}")
    ok, fmt = zk.preflight_book(path)
    if not ok:
        problems.append(f"preflight failed: {fmt}")
    if not zk.epub_namespace_ok(path):
        problems.append("merged OPF does not use the default namespace")
    if os.path.getsize(path) == 0:
        problems.append("merged file is empty")
    return problems


def main():
    results = []
    for out_name, title, author, volumes in COMPILATIONS:
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

        entries = [(os.path.join(LIB, f), vol_title) for f, vol_title in volumes]
        out_path = os.path.join(OUT, out_name)
        epub_merge.merge(entries, out_path, title, author)

        problems = verify_merged(out_path, title, author)

        # If the merge is still too big for the mail API, slim it and check
        # it all over again. The file changed, so the guards must run again.
        for opts in SLIM_PASSES:
            if os.path.getsize(out_path) <= MAX_MERGED_BYTES:
                break
            before = os.path.getsize(out_path)
            slim_epub.slim(out_path, **opts)
            after = os.path.getsize(out_path)
            if after >= before:
                continue
            print(f"    slimmed {before:,} -> {after:,} bytes")
            problems = verify_merged(out_path, title, author)

        size = os.path.getsize(out_path)
        if size > MAX_MERGED_BYTES:
            problems.append(
                f"still {size:,} bytes, over the {MAX_MERGED_BYTES:,} ceiling")

        if problems:
            for p in problems:
                print(f"  ! {out_name}: {p}")
            results.append((out_name, False, "; ".join(problems)))
            continue

        print(f"  ✓ {out_name}  ({size:,} bytes, {len(volumes)} volumes)")
        results.append((out_name, True, f"{size} bytes"))

    print("\n=== built {0}/{1} compilations ===".format(
        sum(1 for _, ok, _ in results if ok), len(results)))
    with open("/tmp/drossprobe/new-compilation-build.json", "w") as fh:
        json.dump([{"file": f, "ok": ok, "detail": d} for f, ok, d in results],
                  fh, indent=1)
    return 0 if all(ok for _, ok, _ in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
