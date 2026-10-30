#!/usr/bin/env python3
"""Build the themed and complete-series compilations, then verify every one.

Every source file is checked against the title and author it was requested
under *before* it goes into a compilation, and every merged compilation is
re-checked afterwards, so a bad merge can never reach the Kindle address.
A merged file that is still too big for the mail API is slimmed and
re-verified before it is accepted.

Partition decisions live in `PARTITIONS` below, and the reason for each
one is recorded next to it. Two of them matter enough to spell out:

* Oz. The library's `Oz-01`..`Oz-12` are the canonical Baum novels one to
  twelve. `Oz-Vol-13`/`Oz-Vol-14` are books thirteen and fourteen and are
  preferred over the six-megabyte `Oz-13`/`Oz-14` duplicates, which carry
  the same two books with heavier scans. `Oz-Extra-01-The-Land-of-Oz` is
  the 1904 combined edition of books one and two and duplicates material
  that is already in the set, so it is excluded entirely.

* Barsoom. Eight books: the seven Barsoom novels plus *The Land That Time
  Forgot*, which the library holds as `Mars-09`.
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

# The mail API in front of Amazon rejects an oversized attachment with a
# 413. 4,130,844 bytes was accepted and 6,757,855 bytes was refused, so
# the ceiling is somewhere in between. Stay well under the lower of those.
#
# This must stay at or below the delivery script's MAX_ATTACHMENT_BYTES, or a
# compilation could be built that the mail API would then refuse.
MAX_MERGED_BYTES = 3_400_000

# Applied to a merged file that is still over the ceiling. Each pass is
# progressively more aggressive. These are the same passes the delivery
# script uses, so a file that builds is a file that can be sent.
SLIM_PASSES = [
    {"threshold": 20_000, "max_edge": 700, "quality": 35},
    {"threshold": 8_000, "max_edge": 500, "quality": 25},
    {"threshold": 1, "max_edge": 380, "quality": 18},
]

# filename -> (accepted internal title fragments, author fragment or None)
SOURCES = {
    # --- angels, demons, devils, heaven, hell -------------------------
    "Seraphita-Balzac.epub": (("seraphita",), "balzac"),
    "The-Angel-and-the-Demon.epub": (("angel and the demon",), "arthur"),
    "Hound-of-Heaven-Thompson.epub": (("hound of heaven",), "thompson"),
    "The-Possessed-Dostoevsky.epub": (("possessed",), "dostoyevsky"),
    "The-Three-Impostors-Machen.epub": (("three impostors",), "machen"),
    "Devil-Stories-Anthology.epub": (("devil stories",), None),
    "Daemonologie-James-VI.epub": (("daemonologie",), "james"),
    "Devil-Worship-in-France.epub": (("devil-worship in france",
                                       "devil worship in france"), "waite"),
    "Sorrows-of-Satan-Corelli.epub": (("sorrows of satan",), "corelli"),
    "Heaven-and-Its-Wonders-and-Hell.epub": (("heaven and its wonders",),
                                               "swedenborg"),
    "Marriage-of-Heaven-and-Hell-Blake.epub": (("marriage of heaven and hell",),
                                               "blake"),
    "Story-of-the-Heavens-Jeans.epub": (("story of the heavens",), "ball"),
    "Great-Controversy-Christ-and-Satan.epub": (("great controversy",), "white"),
    "The-Inferno-Dante-Dore.epub": (("vision of hell", "inferno"), "dante"),

    # --- Oz: the canonical fourteen Baum novels ------------------------
    "Oz-01-Wonderful-Wizard.epub": (("wonderful wizard",), "baum"),
    "Oz-02-Marvelous-Land.epub": (("marvelous land",), "baum"),
    "Oz-03-Ozma-of-Oz.epub": (("ozma of oz",), "baum"),
    "Oz-04-Dorothy-and-the-Wizard.epub": (("dorothy and the wizard",), "baum"),
    "Oz-05-Road-to-Oz.epub": (("road to oz",), "baum"),
    "Oz-06-Emerald-City-of-Oz.epub": (("emerald city",), "baum"),
    "Oz-07-Lost-Princess-of-Oz.epub": (("lost princess",), "baum"),
    "Oz-08-Tik-Tok-of-Oz.epub": (("tik-tok",), "baum"),
    "Oz-09-Rinkitink-in-Oz.epub": (("rinkitink",), "baum"),
    "Oz-10-Magic-of-Oz.epub": (("magic of oz",), "baum"),
    "Oz-11-Tin-Woodman-of-Oz.epub": (("tin woodman",), "baum"),
    "Oz-12-Patchwork-Girl-of-Oz.epub": (("patchwork girl",), "baum"),
    "Oz-Vol-13.epub": (("wishing horse",), "thompson"),
    "Oz-Vol-14.epub": (("ozoplaning",), "thompson"),
    # Oz: the later Land of Oz books, kept apart from the fourteen
    "Oz-Extra-02-The-Scarecrow-of-Oz.epub": (("scarecrow of oz",), "baum"),
    "Oz-Extra-03-The-Royal-Book-of-Oz.epub": (("royal book of oz",),
                                               "thompson"),
    "Oz-Extra-04-Glinda-of-Oz.epub": (("glinda of oz",), "baum"),
    "Oz-Extra-05-The-Woggle-Bug.epub": (("woggle-bug",), "baum"),

    # --- Barsoom: eight books ------------------------------------------
    "Mars-01-Princess-of-Mars.epub": (("princess of mars",), "burroughs"),
    "Mars-02-Gods-of-Mars.epub": (("gods of mars",), "burroughs"),
    "Mars-03-Warlord-of-Mars.epub": (("warlord of mars",), "burroughs"),
    "Mars-04-Thuvia-Maid-of-Mars.epub": (("thuvia",), "burroughs"),
    "Mars-05-Chessmen-of-Mars.epub": (("chessmen of mars",), "burroughs"),
    "Mars-06-Master-Mind-of-Mars.epub": (("master mind",), "burroughs"),
    "Mars-07-Fighting-Man-of-Mars.epub": (("fighting man of mars",),
                                          "burroughs"),
    "Mars-09-Land-That-Time-Forgot.epub": (("land that time forgot",),
                                           "burroughs"),

    # --- the Pellucidar duology ----------------------------------------
    "Pellucidar.epub": (("pellucidar",), "burroughs"),
    "Tanar-of-Pellucidar.epub": (("tanar of pellucidar",), "burroughs"),

    # --- Poe, Bierce, Dunsany ------------------------------------------
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

    # --- Frazer, The Golden Bough, twelve volumes ----------------------
    "Frazer-The-Golden-Bough-Vol-01.epub": (("golden bough",), "frazer"),
    "Frazer-The-Golden-Bough-Vol-02.epub": (("golden bough",), "frazer"),
    "Frazer-The-Golden-Bough-Vol-03.epub": (("golden bough",), "frazer"),
    "Frazer-The-Golden-Bough-Vol-04.epub": (("golden bough",), "frazer"),
    "Frazer-The-Golden-Bough-Vol-05.epub": (("golden bough",), "frazer"),
    "Frazer-The-Golden-Bough-Vol-06.epub": (("golden bough",), "frazer"),
    "Frazer-The-Golden-Bough-Vol-07.epub": (("golden bough",), "frazer"),
    "Frazer-The-Golden-Bough-Vol-08.epub": (("golden bough",), "frazer"),
    "Frazer-The-Golden-Bough-Vol-09.epub": (("golden bough",), "frazer"),
    "Frazer-The-Golden-Bough-Vol-10.epub": (("golden bough",), "frazer"),
    "Frazer-The-Golden-Bough-Vol-11.epub": (("golden bough",), "frazer"),
    "Frazer-The-Golden-Bough-Vol-12.epub": (("golden bough",), "frazer"),

    # --- the Arabian Nights, in two different translations -------------
    "Burton-Thousand-Nights-and-a-Night-Vol-01.epub": (
        ("thousand nights and a night",), None),
    "Burton-Thousand-Nights-and-a-Night-Vol-02.epub": (
        ("thousand nights and a night",), None),
    "Burton-Thousand-Nights-and-a-Night-Vol-03.epub": (
        ("thousand nights and a night",), None),
    "Burton-Thousand-Nights-and-a-Night-Vol-04.epub": (
        ("thousand nights and a night",), None),
    "Burton-Thousand-Nights-and-a-Night-Vol-05.epub": (
        ("thousand nights and a night",), None),
    "Burton-Thousand-Nights-and-a-Night-Vol-06.epub": (
        ("thousand nights and a night",), None),
    "Burton-Thousand-Nights-and-a-Night-Vol-07.epub": (
        ("thousand nights and a night",), None),
    "Burton-Thousand-Nights-and-a-Night-Vol-08.epub": (
        ("thousand nights and a night",), None),
    "Burton-Thousand-Nights-and-a-Night-Vol-09.epub": (
        ("thousand nights and a night",), None),
    "Burton-Thousand-Nights-and-a-Night-Vol-10.epub": (
        ("thousand nights and a night",), None),
    "Payne-Thousand-Nights-and-One-Night-Vol-01.epub": (
        ("thousand nights and one night",), None),
    "Payne-Thousand-Nights-and-One-Night-Vol-02.epub": (
        ("thousand nights and one night",), None),
    "Payne-Thousand-Nights-and-One-Night-Vol-03.epub": (
        ("thousand nights and one night",), None),

    # --- Le Fanu, four sets --------------------------------------------
    "LeFanu-Ghostly-Tales-Vol-01.epub": (("ghostly tales",), "le fanu"),
    "LeFanu-Ghostly-Tales-Vol-02.epub": (("ghostly tales",), "le fanu"),
    "LeFanu-Ghostly-Tales-Vol-03.epub": (("ghostly tales",), "le fanu"),
    "LeFanu-Ghostly-Tales-Vol-04.epub": (("ghostly tales",), "le fanu"),
    "LeFanu-Ghostly-Tales-Vol-05.epub": (("ghostly tales",), "le fanu"),
    "LeFanu-In-a-Glass-Darkly-Vol-01.epub": (("in a glass darkly",), "le fanu"),
    "LeFanu-In-a-Glass-Darkly-Vol-02.epub": (("in a glass darkly",), "le fanu"),
    "LeFanu-In-a-Glass-Darkly-Vol-03.epub": (("in a glass darkly",), "le fanu"),
    "LeFanu-The-Purcell-Papers-Vol-01.epub": (("purcell papers",), "le fanu"),
    "LeFanu-The-Purcell-Papers-Vol-02.epub": (("purcell papers",), "le fanu"),
    "LeFanu-The-Purcell-Papers-Vol-03.epub": (("purcell papers",), "le fanu"),
    "LeFanu-The-Tenants-of-Malory-Vol-01.epub": (("tenants of malory",),
                                                 "le fanu"),
    "LeFanu-The-Tenants-of-Malory-Vol-02.epub": (("tenants of malory",),
                                                 "le fanu"),
    "LeFanu-The-Tenants-of-Malory-Vol-03.epub": (("tenants of malory",),
                                                 "le fanu"),

    # --- Malory, Mabinogion, Kalevala, Decameron -----------------------
    "Malory-Le-Morte-dArthur-Vol-01.epub": (("morte d'arthur",), "malory"),
    "Malory-Le-Morte-dArthur-Vol-02.epub": (("morte d'arthur",), "malory"),
    "Mabinogion-The-Mabinogion-Vol-01.epub": (("mabinogion",), None),
    "Mabinogion-The-Mabinogion-Vol-02.epub": (("mabinogion",), None),
    "Mabinogion-The-Mabinogion-Vol-03.epub": (("mabinogion",), None),
    "Kalevala-Land-of-the-Heroes-Vol-01.epub": (("kalevala",), None),
    "Kalevala-Land-of-the-Heroes-Vol-02.epub": (("kalevala",), None),
    "Boccaccio-The-Decameron-Vol-01.epub": (("decameron",), "boccaccio"),
    "Boccaccio-The-Decameron-Vol-02.epub": (("decameron",), "boccaccio"),

    # --- Spenser, Andersen, M. R. James, Persian -----------------------
    "Spenser-The-Faerie-Queene-Vol-01.epub": (("faerie queene",), "spenser"),
    "Spenser-The-Faerie-Queene-Vol-02.epub": (("faerie queene",), "spenser"),
    "Andersen-Fairy-Tales-Vol-01.epub": (("fairy tales",), "andersen"),
    "Andersen-Fairy-Tales-Vol-02.epub": (("fairy tales",), "andersen"),
    "MRJames-Ghost-Stories-of-an-Antiquary-Vol-01.epub": (
        ("ghost stories of an antiquary",), "james"),
    "MRJames-Ghost-Stories-of-an-Antiquary-Vol-02.epub": (
        ("ghost stories of an antiquary",), "james"),
    "Persian-Literature-Vol-01.epub": (("persian literature",), None),
    "Persian-Literature-Vol-02.epub": (("persian literature",), None),

    # --- Faust, the German original in a matched pair ------------------
    "Faust-German-01-Erster-Teil.epub": (("tragödie erster teil",), "goethe"),
    "Faust-German-02-Zweiter-Teil.epub": (("tragödie zweiter teil",), "goethe"),

    # --- Herodotus, Gibbon ---------------------------------------------
    "Herodotus-Vol-01.epub": (("herodotus",), "herodotus"),
    "Herodotus-Vol-02.epub": (("herodotus",), "herodotus"),
    "Gibbon-Decline-and-Fall-Vol-01.epub": (("decline and fall",), "gibbon"),
    "Gibbon-Decline-and-Fall-Vol-02.epub": (("decline and fall",), "gibbon"),
    "Gibbon-Decline-and-Fall-Vol-03.epub": (("decline and fall",), "gibbon"),
    "Gibbon-Decline-and-Fall-Vol-04.epub": (("decline and fall",), "gibbon"),
    "Gibbon-Decline-and-Fall-Vol-05.epub": (("decline and fall",), "gibbon"),
    "Gibbon-Decline-and-Fall-Vol-06.epub": (("decline and fall",), "gibbon"),

    # --- the Mahabharata, four volumes ---------------------------------
    "Mahabharata-Vol-01.epub": (("mahabharata",), None),
    "Mahabharata-Vol-02.epub": (("mahabharata",), None),
    "Mahabharata-Vol-03.epub": (("mahabharata",), None),
    "Mahabharata-Vol-04.epub": (("mahabharata",), None),

    # --- the Norse collections -----------------------------------------
    "Norse-Heimskringla.epub": (("heimskringla",), "snorri"),
    "Norse-Story-of-the-Volsungs.epub": (("story of the volsung",), None),
    "Norse-Nibelungenlied.epub": (("nibelungenlied",), None),
    "Norse-Saga-of-Grettir-the-Strong.epub": (("grettir",), None),
    "Norse-Fridthjofs-Saga.epub": (("fridthjof",), "tegn"),
    "Norse-Popular-Tales-from-the-Norse.epub": (
        ("popular tales from the norse",), None),

    # --- Grote, History of Greece, complete in twelve volumes ---------
    "Grote-History-of-Greece-Vol-01.epub": (("history of greece",), "grote"),
    "Grote-History-of-Greece-Vol-02.epub": (("history of greece",), "grote"),
    "Grote-History-of-Greece-Vol-03.epub": (("history of greece",), "grote"),
    "Grote-History-of-Greece-Vol-04.epub": (("history of greece",), "grote"),
    "Grote-History-of-Greece-Vol-05.epub": (("history of greece",), "grote"),
    "Grote-History-of-Greece-Vol-06.epub": (("history of greece",), "grote"),
    "Grote-History-of-Greece-Vol-07.epub": (("history of greece",), "grote"),
    "Grote-History-of-Greece-Vol-08.epub": (("history of greece",), "grote"),
    "Grote-History-of-Greece-Vol-09.epub": (("history of greece",), "grote"),
    "Grote-History-of-Greece-Vol-10.epub": (("history of greece",), "grote"),
    "Grote-History-of-Greece-Vol-11.epub": (("history of greece",), "grote"),
    "Grote-History-of-Greece-Vol-12.epub": (("history of greece",), "grote"),

    # --- Valmiki, The Ramayana, complete in four volumes (Dutt) --------
    "Ramayana-Vol-01-Balakandam-and-Ayodhyakandam.epub": (
        ("r\u0101m\u0101yana", "ramayana"), "valmiki"),
    "Ramayana-Vol-02-Aranya-Kishkindha-and-Sundara.epub": (
        ("r\u0101m\u0101yana", "ramayana"), "valmiki"),
    "Ramayana-Vol-03-Yuddhakandam.epub": (
        ("r\u0101m\u0101yana", "ramayana"), "valmiki"),
    "Ramayana-Vol-04-Uttara-Kanda.epub": (
        ("r\u0101m\u0101yana", "ramayana"), "valmiki"),

    # --- Valmiki, the Maharamayana / Yoga-Vasishtha, four volumes -----
    "Maharamayana-Vol-01.epub": (("maharamayana",), "valmiki"),
    "Maharamayana-Vol-02-Part-1.epub": (("maharamayana",), "valmiki"),
    "Maharamayana-Vol-02-Part-2.epub": (("maharamayana",), "valmiki"),
    "Maharamayana-Vol-03-Part-1.epub": (("maharamayana",), "valmiki"),
    "Maharamayana-Vol-03-Part-2.epub": (("maharamayana",), "valmiki"),
    "Maharamayana-Vol-04-Part-1.epub": (("maharamayana",), "valmiki"),
    "Maharamayana-Vol-04-Part-2.epub": (("maharamayana",), "valmiki"),

    # --- the last seven sources the coverage sweep found uncovered -----
    # Each of these was checked against the union of the 57 delivered
    # compilations with normalised text and 8-word shingles before it was
    # accepted here: none of them is contained by anything already sent.
    "Kalevala-Complete.epub": (("kalevala",), "elias"),
    "Andersen-Fairy-Tales-Omnibus.epub": (("andersen",), "andersen"),
    "MRJames-A-Thin-Ghost-and-Others.epub": (("thin ghost",), "james"),
    "MRJames-A-Warning-to-the-Curious.epub": (
        ("warning to the curious",), "james"),
    "Faust-Part-1-English-Goethe.epub": (("faust",), "goethe"),
    "Samson-Agonistes-Milton-Poetical-Works.epub": (
        ("poetical works",), "milton"),
    "Shakespeare-Complete-Works.epub": (("complete works",), "shakespeare"),
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

    # --- Oz, the canonical fourteen in three parts ---------------------
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

    ("The-Oz-Series-Part-III-Books-13-to-14.epub",
     "The Oz Series, Part III: Books Thirteen and Fourteen",
     "L. Frank Baum and Ruth Plumly Thompson",
     [("Oz-Vol-13.epub", "The Wishing Horse of Oz"),
      ("Oz-Vol-14.epub", "Ozoplaning with the Wizard of Oz")]),

    ("The-Later-Oz-Books.epub",
     "The Later Oz Books: The Scarecrow, the Royal Book, Glinda and the Woggle-Bug",
     "L. Frank Baum and Ruth Plumly Thompson",
     [("Oz-Extra-02-The-Scarecrow-of-Oz.epub", "The Scarecrow of Oz"),
      ("Oz-Extra-03-The-Royal-Book-of-Oz.epub", "The Royal Book of Oz"),
      ("Oz-Extra-04-Glinda-of-Oz.epub", "Glinda of Oz"),
      ("Oz-Extra-05-The-Woggle-Bug.epub", "The Woggle-Bug Book")]),

    # --- Barsoom, eight books -------------------------------------------
    ("The-Barsoom-Chronicles.epub",
     "The Barsoom Chronicles",
     "Edgar Rice Burroughs",
     [("Mars-01-Princess-of-Mars.epub", "A Princess of Mars"),
      ("Mars-02-Gods-of-Mars.epub", "The Gods of Mars"),
      ("Mars-03-Warlord-of-Mars.epub", "The Warlord of Mars"),
      ("Mars-04-Thuvia-Maid-of-Mars.epub", "Thuvia, Maid of Mars"),
      ("Mars-05-Chessmen-of-Mars.epub", "The Chessmen of Mars"),
      ("Mars-06-Master-Mind-of-Mars.epub", "The Master Mind of Mars"),
      ("Mars-07-Fighting-Man-of-Mars.epub", "A Fighting Man of Mars"),
      ("Mars-09-Land-That-Time-Forgot.epub", "The Land That Time Forgot")]),

    # --- the Pellucidar duology ----------------------------------------
    ("The-Pellucidar-Series.epub",
     "The Pellucidar Series",
     "Edgar Rice Burroughs",
     [("Pellucidar.epub", "Pellucidar"),
      ("Tanar-of-Pellucidar.epub", "Tanar of Pellucidar")]),

    # --- the Mahabharata, in two parts ---------------------------------
    ("The-Mahabharata-Part-I-Volumes-1-to-2.epub",
     "The Mahabharata, Part I: Volumes One and Two",
     "Krishna-Dwaipayana Vyasa",
     [("Mahabharata-Vol-01.epub",
       "The Mahabharata, Volume 1: Books 1, 2 and 3"),
      ("Mahabharata-Vol-02.epub",
       "The Mahabharata, Volume 2: Books 4, 5, 6 and 7")]),

    ("The-Mahabharata-Part-II-Volumes-3-to-4.epub",
     "The Mahabharata, Part II: Volumes Three and Four",
     "Krishna-Dwaipayana Vyasa",
     [("Mahabharata-Vol-03.epub",
       "The Mahabharata, Volume 3: Books 8, 9, 10, 11 and 12"),
      ("Mahabharata-Vol-04.epub",
       "The Mahabharata, Volume 4: Books 13, 14, 15, 16, 17 and 18")]),

    # --- Gibbon, in three parts -----------------------------------------
    ("The-Decline-and-Fall-Volumes-1-to-2.epub",
     "The Decline and Fall of the Roman Empire, Part I: Volumes One and Two",
     "Edward Gibbon",
     [("Gibbon-Decline-and-Fall-Vol-01.epub",
       "The Decline and Fall of the Roman Empire, Volume 1"),
      ("Gibbon-Decline-and-Fall-Vol-02.epub",
       "The Decline and Fall of the Roman Empire, Volume 2")]),

    ("The-Decline-and-Fall-Volumes-3-to-4.epub",
     "The Decline and Fall of the Roman Empire, Part II: Volumes Three and Four",
     "Edward Gibbon",
     [("Gibbon-Decline-and-Fall-Vol-03.epub",
       "The Decline and Fall of the Roman Empire, Volume 3"),
      ("Gibbon-Decline-and-Fall-Vol-04.epub",
       "The Decline and Fall of the Roman Empire, Volume 4")]),

    ("The-Decline-and-Fall-Volumes-5-to-6.epub",
     "The Decline and Fall of the Roman Empire, Part III: Volumes Five and Six",
     "Edward Gibbon",
     [("Gibbon-Decline-and-Fall-Vol-05.epub",
       "The Decline and Fall of the Roman Empire, Volume 5"),
      ("Gibbon-Decline-and-Fall-Vol-06.epub",
       "The Decline and Fall of the Roman Empire, Volume 6")]),

    # --- Herodotus ------------------------------------------------------
    ("The-History-of-Herodotus.epub",
     "The History of Herodotus",
     "Herodotus",
     [("Herodotus-Vol-01.epub", "The History of Herodotus, Volume 1"),
      ("Herodotus-Vol-02.epub", "The History of Herodotus, Volume 2")]),

    # --- the Norse collections -----------------------------------------
    ("The-Norse-Sagas-and-Tales.epub",
     "The Norse Sagas and Tales",
     "Various Authors",
     [("Norse-Heimskringla.epub",
       "Heimskringla, or the Chronicle of the Kings of Norway"),
      ("Norse-Story-of-the-Volsungs.epub", "The Story of the Volsungs"),
      ("Norse-Nibelungenlied.epub", "The Nibelungenlied"),
      ("Norse-Saga-of-Grettir-the-Strong.epub",
       "The Saga of Grettir the Strong"),
      ("Norse-Fridthjofs-Saga.epub", "Frithjof's Saga"),
      ("Norse-Popular-Tales-from-the-Norse.epub",
       "Popular Tales from the Norse")]),

    # --- the Golden Bough, in four parts --------------------------------
    ("The-Golden-Bough-Volumes-1-to-3.epub",
     "The Golden Bough, Part I: Volumes One to Three",
     "James George Frazer",
     [("Frazer-The-Golden-Bough-Vol-01.epub",
       "The Golden Bough, Volume 1"),
      ("Frazer-The-Golden-Bough-Vol-02.epub",
       "The Golden Bough, Volume 2"),
      ("Frazer-The-Golden-Bough-Vol-03.epub",
       "The Golden Bough, Volume 3")]),

    ("The-Golden-Bough-Volumes-4-to-6.epub",
     "The Golden Bough, Part II: Volumes Four to Six",
     "James George Frazer",
     [("Frazer-The-Golden-Bough-Vol-04.epub",
       "The Golden Bough, Volume 4"),
      ("Frazer-The-Golden-Bough-Vol-05.epub",
       "The Golden Bough, Volume 5"),
      ("Frazer-The-Golden-Bough-Vol-06.epub",
       "The Golden Bough, Volume 6")]),

    ("The-Golden-Bough-Volumes-7-to-9.epub",
     "The Golden Bough, Part III: Volumes Seven to Nine",
     "James George Frazer",
     [("Frazer-The-Golden-Bough-Vol-07.epub",
       "The Golden Bough, Volume 7"),
      ("Frazer-The-Golden-Bough-Vol-08.epub",
       "The Golden Bough, Volume 8"),
      ("Frazer-The-Golden-Bough-Vol-09.epub",
       "The Golden Bough, Volume 9")]),

    ("The-Golden-Bough-Volumes-10-to-12.epub",
     "The Golden Bough, Part IV: Volumes Ten to Twelve",
     "James George Frazer",
     [("Frazer-The-Golden-Bough-Vol-10.epub",
       "The Golden Bough, Volume 10"),
      ("Frazer-The-Golden-Bough-Vol-11.epub",
       "The Golden Bough, Volume 11"),
      ("Frazer-The-Golden-Bough-Vol-12.epub",
       "The Golden Bough, Volume 12")]),

    # --- the Arabian Nights, in two translations ------------------------
    ("The-Thousand-Nights-and-a-Night-Volumes-1-to-5.epub",
     "The Book of the Thousand Nights and a Night, Part I: Volumes One to Five",
     "Richard Francis Burton",
     [("Burton-Thousand-Nights-and-a-Night-Vol-01.epub",
       "The Thousand Nights and a Night, Volume 1"),
      ("Burton-Thousand-Nights-and-a-Night-Vol-02.epub",
       "The Thousand Nights and a Night, Volume 2"),
      ("Burton-Thousand-Nights-and-a-Night-Vol-03.epub",
       "The Thousand Nights and a Night, Volume 3"),
      ("Burton-Thousand-Nights-and-a-Night-Vol-04.epub",
       "The Thousand Nights and a Night, Volume 4"),
      ("Burton-Thousand-Nights-and-a-Night-Vol-05.epub",
       "The Thousand Nights and a Night, Volume 5")]),

    ("The-Thousand-Nights-and-a-Night-Volumes-6-to-10.epub",
     "The Book of the Thousand Nights and a Night, Part II: Volumes Six to Ten",
     "Richard Francis Burton",
     [("Burton-Thousand-Nights-and-a-Night-Vol-06.epub",
       "The Thousand Nights and a Night, Volume 6"),
      ("Burton-Thousand-Nights-and-a-Night-Vol-07.epub",
       "The Thousand Nights and a Night, Volume 7"),
      ("Burton-Thousand-Nights-and-a-Night-Vol-08.epub",
       "The Thousand Nights and a Night, Volume 8"),
      ("Burton-Thousand-Nights-and-a-Night-Vol-09.epub",
       "The Thousand Nights and a Night, Volume 9"),
      ("Burton-Thousand-Nights-and-a-Night-Vol-10.epub",
       "The Thousand Nights and a Night, Volume 10")]),

    ("The-Thousand-Nights-and-One-Night.epub",
     "The Book of the Thousand Nights and One Night",
     "Richard Francis Burton",
     [("Payne-Thousand-Nights-and-One-Night-Vol-01.epub",
       "The Thousand Nights and One Night, Volume I"),
      ("Payne-Thousand-Nights-and-One-Night-Vol-02.epub",
       "The Thousand Nights and One Night, Volume II"),
      ("Payne-Thousand-Nights-and-One-Night-Vol-03.epub",
       "The Thousand Nights and One Night, Volume III")]),

    # --- Le Fanu --------------------------------------------------------
    ("The-Ghostly-Tales-of-Le-Fanu.epub",
     "The Ghostly Tales of Joseph Sheridan Le Fanu",
     "Joseph Sheridan Le Fanu",
     [("LeFanu-Ghostly-Tales-Vol-01.epub",
       "Ghostly Tales, Volume 1"),
      ("LeFanu-Ghostly-Tales-Vol-02.epub",
       "Ghostly Tales, Volume 2"),
      ("LeFanu-Ghostly-Tales-Vol-03.epub",
       "Ghostly Tales, Volume 3"),
      ("LeFanu-Ghostly-Tales-Vol-04.epub",
       "Ghostly Tales, Volume 4"),
      ("LeFanu-Ghostly-Tales-Vol-05.epub",
       "Ghostly Tales, Volume 5")]),

    ("In-a-Glass-Darkly.epub",
     "In a Glass Darkly",
     "Joseph Sheridan Le Fanu",
     [("LeFanu-In-a-Glass-Darkly-Vol-01.epub",
       "In a Glass Darkly, Volume 1"),
      ("LeFanu-In-a-Glass-Darkly-Vol-02.epub",
       "In a Glass Darkly, Volume 2"),
      ("LeFanu-In-a-Glass-Darkly-Vol-03.epub",
       "In a Glass Darkly, Volume 3")]),

    ("The-Purcell-Papers.epub",
     "The Purcell Papers",
     "Joseph Sheridan Le Fanu",
     [("LeFanu-The-Purcell-Papers-Vol-01.epub",
       "The Purcell Papers, Volume 1"),
      ("LeFanu-The-Purcell-Papers-Vol-02.epub",
       "The Purcell Papers, Volume 2"),
      ("LeFanu-The-Purcell-Papers-Vol-03.epub",
       "The Purcell Papers, Volume 3")]),

    ("The-Tenants-of-Malory.epub",
     "The Tenants of Malory",
     "Joseph Sheridan Le Fanu",
     [("LeFanu-The-Tenants-of-Malory-Vol-01.epub",
       "The Tenants of Malory, Volume 1"),
      ("LeFanu-The-Tenants-of-Malory-Vol-02.epub",
       "The Tenants of Malory, Volume 2"),
      ("LeFanu-The-Tenants-of-Malory-Vol-03.epub",
       "The Tenants of Malory, Volume 3")]),

    # --- Malory, Mabinogion, Kalevala, Decameron -----------------------
    ("Le-Morte-dArthur.epub",
     "Le Morte d'Arthur",
     "Sir Thomas Malory",
     [("Malory-Le-Morte-dArthur-Vol-01.epub",
       "Le Morte d'Arthur, Volume 1"),
      ("Malory-Le-Morte-dArthur-Vol-02.epub",
       "Le Morte d'Arthur, Volume 2")]),

    ("The-Mabinogion.epub",
     "The Mabinogion",
     "Various Authors",
     [("Mabinogion-The-Mabinogion-Vol-01.epub", "The Mabinogion, Volume 1"),
      ("Mabinogion-The-Mabinogion-Vol-02.epub", "The Mabinogion, Volume 2"),
      ("Mabinogion-The-Mabinogion-Vol-03.epub", "The Mabinogion, Volume 3")]),

    ("Kalevala-The-Land-of-the-Heroes.epub",
     "Kalevala, the Land of the Heroes",
     "Elias Lonnrot",
     [("Kalevala-Land-of-the-Heroes-Vol-01.epub",
       "Kalevala, Volume One"),
      ("Kalevala-Land-of-the-Heroes-Vol-02.epub",
       "Kalevala, Volume Two")]),

    ("The-Decameron.epub",
     "The Decameron",
     "Giovanni Boccaccio",
     [("Boccaccio-The-Decameron-Vol-01.epub", "The Decameron, Volume I"),
      ("Boccaccio-The-Decameron-Vol-02.epub", "The Decameron, Volume II")]),

    # --- Spenser, Andersen, M. R. James, Persian -----------------------
    ("The-Faerie-Queene.epub",
     "The Faerie Queene",
     "Edmund Spenser",
     [("Spenser-The-Faerie-Queene-Vol-01.epub",
       "The Faerie Queene, Volume 1"),
      ("Spenser-The-Faerie-Queene-Vol-02.epub",
       "The Faerie Queene, Volume 2")]),

    ("The-Fairy-Tales-of-Hans-Andersen.epub",
     "The Fairy Tales of Hans Christian Andersen",
     "Hans Christian Andersen",
     [("Andersen-Fairy-Tales-Vol-01.epub",
       "Hans Andersen's Fairy Tales, First Series"),
      ("Andersen-Fairy-Tales-Vol-02.epub",
       "Hans Andersen's Fairy Tales, Second Series")]),

    ("Ghost-Stories-of-an-Antiquary.epub",
     "Ghost Stories of an Antiquary",
     "M. R. James",
     [("MRJames-Ghost-Stories-of-an-Antiquary-Vol-01.epub",
       "Ghost Stories of an Antiquary, Part 1"),
      ("MRJames-Ghost-Stories-of-an-Antiquary-Vol-02.epub",
       "Ghost Stories of an Antiquary, Part 2")]),

    ("The-Persian-Literature.epub",
     "The Persian Literature",
     "Various Authors",
     [("Persian-Literature-Vol-01.epub", "The Persian Literature, Volume 1"),
      ("Persian-Literature-Vol-02.epub", "The Persian Literature, Volume 2")]),

    # --- Faust, the German original, both halves -----------------------
    ("Faust-Der-Tragoedie-Complete.epub",
     "Faust: Der Tragodie, Parts One and Two",
     "Johann Wolfgang von Goethe",
     [("Faust-German-01-Erster-Teil.epub",
       "Faust: Der Tragodie, erster Teil"),
      ("Faust-German-02-Zweiter-Teil.epub",
       "Faust: Der Tragodie, zweiter Teil")]),

    # --- Poe, Bierce, Dunsany -------------------------------------------
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

    # --- Grote, History of Greece, complete in twelve volumes ---------
    ("The-History-of-Greece-Volumes-1-to-3.epub",
     "The History of Greece, Volumes One to Three",
     "George Grote",
     [("Grote-History-of-Greece-Vol-01.epub",
       "History of Greece, Volume 1"),
      ("Grote-History-of-Greece-Vol-02.epub",
       "History of Greece, Volume 2"),
      ("Grote-History-of-Greece-Vol-03.epub",
       "History of Greece, Volume 3")]),

    ("The-History-of-Greece-Volumes-4-to-6.epub",
     "The History of Greece, Volumes Four to Six",
     "George Grote",
     [("Grote-History-of-Greece-Vol-04.epub",
       "History of Greece, Volume 4"),
      ("Grote-History-of-Greece-Vol-05.epub",
       "History of Greece, Volume 5"),
      ("Grote-History-of-Greece-Vol-06.epub",
       "History of Greece, Volume 6")]),

    ("The-History-of-Greece-Volumes-7-to-9.epub",
     "The History of Greece, Volumes Seven to Nine",
     "George Grote",
     [("Grote-History-of-Greece-Vol-07.epub",
       "History of Greece, Volume 7"),
      ("Grote-History-of-Greece-Vol-08.epub",
       "History of Greece, Volume 8"),
      ("Grote-History-of-Greece-Vol-09.epub",
       "History of Greece, Volume 9")]),

    ("The-History-of-Greece-Volumes-10-to-12.epub",
     "The History of Greece, Volumes Ten to Twelve",
     "George Grote",
     [("Grote-History-of-Greece-Vol-10.epub",
       "History of Greece, Volume 10"),
      ("Grote-History-of-Greece-Vol-11.epub",
       "History of Greece, Volume 11"),
      ("Grote-History-of-Greece-Vol-12.epub",
       "History of Greece, Volume 12")]),

    # --- Valmiki, The Ramayana, complete in four volumes --------------
    ("The-Ramayana-Volumes-1-to-2.epub",
     "The Ramayana, Volumes One and Two: Balakandam, Ayodhyakandam, Aranya, Kishkindha and Sundara",
     "Valmiki, translated by Manmatha Nath Dutt",
     [("Ramayana-Vol-01-Balakandam-and-Ayodhyakandam.epub",
       "The Ramayana, Volume 1: Balakandam and Ayodhyakandam"),
      ("Ramayana-Vol-02-Aranya-Kishkindha-and-Sundara.epub",
       "The Ramayana, Volume 2: Aranya, Kishkindha and Sundara")]),

    ("The-Ramayana-Volumes-3-to-4.epub",
     "The Ramayana, Volumes Three and Four: Yuddhakandam and Uttara Kanda",
     "Valmiki, translated by Manmatha Nath Dutt",
     [("Ramayana-Vol-03-Yuddhakandam.epub",
       "The Ramayana, Volume 3: Yuddhakandam"),
      ("Ramayana-Vol-04-Uttara-Kanda.epub",
       "The Ramayana, Volume 4: Uttara Kanda")]),

    # --- Valmiki, the Maharamayana (Yoga-Vasishtha), four volumes -----
    ("The-Maharamayana-Volumes-1-to-2.epub",
     "The Maharamayana of Valmiki, Volumes One and Two",
     "Valmiki, translated by Viharilala Mitra",
     [("Maharamayana-Vol-01.epub",
       "The Yoga-Vasishtha Maharamayana of Valmiki, Volume 1"),
      ("Maharamayana-Vol-02-Part-1.epub",
       "The Yoga-Vasishtha Maharamayana of Valmiki, Volume 2, Part 1"),
      ("Maharamayana-Vol-02-Part-2.epub",
       "The Yoga-Vasishtha Maharamayana of Valmiki, Volume 2, Part 2")]),

    ("The-Maharamayana-Volumes-3-to-4.epub",
     "The Maharamayana of Valmiki, Volumes Three and Four",
     "Valmiki, translated by Viharilala Mitra",
     [("Maharamayana-Vol-03-Part-1.epub",
       "The Yoga-Vasishtha Maharamayana of Valmiki, Volume 3, Part 1"),
      ("Maharamayana-Vol-03-Part-2.epub",
       "The Yoga-Vasishtha Maharamayana of Valmiki, Volume 3, Part 2"),
      ("Maharamayana-Vol-04-Part-1.epub",
       "The Yoga-Vasishtha Maharamayana of Valmiki, Volume 4, Part 1"),
      ("Maharamayana-Vol-04-Part-2.epub",
       "The Yoga-Vasishtha Maharamayana of Valmiki, Volume 4, Part 2")]),

    # --- the final seven sources the coverage sweep found uncovered ----
    # Grouping is by author and by shelf: Kalevala stands alone because it
    # is a national epic in its own right; Shakespeare and Milton each
    # stand alone because either one alone already fills most of the
    # attachment ceiling, so they cannot share a volume; Andersen's
    # omnibus rides with the two M. R. James collections as one
    # "stories" volume; and the English Faust stands alone because it is
    # the only complete Faust in English that Gutenberg holds.
    ("The-Kalevala.epub",
     "The Kalevala: The Epic Poem of Finland",
     "Elias Lönnrot",
     [("Kalevala-Complete.epub",
       "The Kalevala: The Epic Poem of Finland, Complete")]),

    ("Fairy-Tales-and-Ghost-Stories.epub",
     "Hans Andersen's Fairy Tales and The Ghost Stories of M. R. James",
     "Hans Christian Andersen and M. R. James",
     [("Andersen-Fairy-Tales-Omnibus.epub",
       "Hans Andersen's Fairy Tales: The Complete Omnibus"),
      ("MRJames-A-Thin-Ghost-and-Others.epub",
       "A Thin Ghost and Others by M. R. James"),
      ("MRJames-A-Warning-to-the-Curious.epub",
       "A Warning to the Curious, and Other Ghost Stories, by M. R. James")]),

    ("Faust-in-English-Part-One.epub",
     "Faust, Part One in English",
     "Johann Wolfgang von Goethe",
     [("Faust-Part-1-English-Goethe.epub",
       "Faust, Part One: An English Translation")]),

    ("The-Poetical-Works-of-John-Milton.epub",
     "The Poetical Works of John Milton",
     "John Milton",
     [("Samson-Agonistes-Milton-Poetical-Works.epub",
       "The Poetical Works of John Milton, Complete")]),

    ("The-Complete-Works-of-William-Shakespeare.epub",
     "The Complete Works of William Shakespeare",
     "William Shakespeare",
     [("Shakespeare-Complete-Works.epub",
       "The Complete Works of William Shakespeare")]),
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
    only = sys.argv[1:]
    results = []
    for out_name, title, author, volumes in COMPILATIONS:
        if only and not any(o in out_name for o in only):
            continue
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

    good = sum(1 for _, ok, _ in results if ok)
    print("\n=== built {0}/{1} compilations ===".format(good, len(results)))
    with open("/tmp/drossprobe/new-compilation-build.json", "w") as fh:
        json.dump([{"file": f, "ok": ok, "detail": d} for f, ok, d in results],
                  fh, indent=1)
    return 0 if good == len(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
