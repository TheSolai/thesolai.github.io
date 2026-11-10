#!/usr/bin/env python3
"""
amre-memory-ledger.py — build and query the Amre memory ledger.

The ledger (~/Desktop/amre.md) holds one memory per line:

    - [type|sensitivity] The memory.

This script parses that file into structured records and, on request, indexes
them into a Chroma vector store where EACH MEMORY IS ONE EMBEDDING. That
last part matters: a character-chunking splitter would glue several memories
into one 500-character blob and retrieval would return a smear of three
unrelated facts instead of the one that answers the question.

Subcommands
    build     parse the ledger -> JSONL (one JSON object per line)
    index     build + embed every memory into the vector store
    query     retrieve the N memories closest to a question
    show      print a memory by id or list by type/sensitivity

Privacy
    The ledger contains medical, trauma and legal material. It lives on the
    Desktop, is gitignored in every repo it might otherwise land in, and the
    vector store is written to a directory that the workspace backup
    excludes. Never publish it.
"""

import argparse
import json
import os
import re
import sys
import urllib.request

LEDGER = os.path.expanduser("~/Desktop/amre.md")
JSONL = os.path.expanduser("~/Desktop/amre.memories.jsonl")
CHROMA_DIR = os.path.expanduser("~/.openclaw/memory-index/amre")

READER_MODEL = os.environ.get("MEMORY_READER_MODEL", "nomic-embed-text")

# nomic-embed-text is trained with task prefixes. Without them the model
# treats both sides as plain text and retrieval quality collapses: a query
# about communication preferences returns Amre's email addresses, because
# "email" appears in the query and the document titles win on surface
# tokens instead of meaning. "search_query:" on the question side and
# "search_document:" on the memory side is the documented pairing.
# Any model that does not want the prefix is detected below and left alone.
QUERY_PREFIX = "search_query: "
DOCUMENT_PREFIX = "search_document: "


def _prefix_for(model):
    """Return the query/document prefixes a model wants, or None for none."""
    name = (model or "").lower()
    if "nomic" in name:
        return QUERY_PREFIX, DOCUMENT_PREFIX
    return None, None


def _ollama_embed(text, model):
    """Embed one string with Ollama's /api/embeddings endpoint."""
    body = json.dumps({"model": model, "prompt": text}).encode()
    req = urllib.request.Request(
        "http://localhost:11434/api/embeddings",
        data=body,
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        return json.loads(resp.read())["embedding"]


def make_embeddings(model=READER_MODEL, prefix=None):
    """A Chroma embedding function backed by Ollama. No langchain dependency.

    This replaced a `langchain_ollama.OllamaEmbeddings` wrapper on 2026-11-09.
    `langchain_chroma` and `langchain_ollama` are **not installed on this machine**
    (verified by `mdfind` and by importing under every venv on the box), so the
    original `index` and `query` paths could not run at all — `query` died with
    `ModuleNotFoundError: No module named 'langchain_chroma'` against a perfectly
    good 164-document index.

    `chromadb` IS available (Learnage venv and /usr/bin/python3), and the on-disk
    index is plain Chroma storage, so the chromadb API reads it directly. The
    task-prefix behaviour the original implementation had is preserved here:
    `search_query:` on the question side, `search_document:` on the memory side
    for nomic models.
    """
    import chromadb

    if prefix is None:
        qp, _ = _prefix_for(model)
        prefix = qp or ""

    class _OllamaEF(chromadb.EmbeddingFunction):
        def __init__(self):
            self.model = model
            self.prefix = prefix

        def name(self):
            # Stable name. Chroma persists the collection's embedding-function
            # config and refuses a get_collection() whose function has a
            # different name ("Embedding function conflict: new: NotImplemented
            # vs persisted: default"). Naming it explicitly makes the index-side
            # and query-side functions agree. The prefix still differs between
            # them, which is correct: documents and questions use different
            # prefixes.
            return "ollama/" + model

        def __call__(self, input):
            return [_ollama_embed(self.prefix + t, self.model) for t in input]

    return _OllamaEF()

# - [type|sensitivity] text    (extra |flags allowed, e.g. |reported|historical)
LINE_RE = re.compile(r"^\s*-\s*\[([^\]]+)\]\s*(.+?)\s*$")

VALID_TYPES = {
    "identity", "family", "health", "medication", "mental-health", "legal",
    "project", "system", "preference", "instruction", "quote", "relationship",
    "assessment", "interest", "unknown",
}


def parse_ledger(path=LEDGER):
    """Parse the ledger into a list of memory records."""
    if not os.path.exists(path):
        raise SystemExit(f"Ledger not found: {path}")

    memories = []
    section = ""
    with open(path, encoding="utf-8") as f:
        for lineno, raw in enumerate(f, 1):
            line = raw.rstrip("\n")
            stripped = line.strip()

            # A heading starts a new section; remember it for the record.
            if stripped.startswith("## "):
                section = stripped[3:].strip()
                continue

            # Blank lines and the header block are not memories.
            if not stripped or stripped.startswith("#"):
                continue

            m = LINE_RE.match(stripped)
            if not m:
                # A line that opens with "- [" was meant to be a memory and
                # is malformed: that is worth reporting. Anything else is
                # ordinary prose (the header block, the rule lines) and is
                # skipped silently.
                if stripped.startswith("- ["):
                    print(f"  ! malformed memory line {lineno}: {stripped[:70]}",
                          file=sys.stderr)
                continue

            tags = [t.strip() for t in m.group(1).split("|") if t.strip()]
            text = m.group(2)

            mtype = tags[0] if tags else "unknown"
            sens = tags[1] if len(tags) > 1 else "public"
            flags = tags[2:]

            if mtype not in VALID_TYPES:
                print(f"  ! line {lineno}: unknown type '{mtype}', "
                      f"treating as unknown", file=sys.stderr)
                mtype = "unknown"
            if sens not in ("public", "private"):
                print(f"  ! line {lineno}: unknown sensitivity '{sens}', "
                      f"treating as private (fail closed)", file=sys.stderr)
                sens = "private"

            memories.append({
                "id": f"amre-{len(memories) + 1:03d}",
                "text": text,
                "type": mtype,
                "sensitivity": sens,
                "flags": flags,
                "section": section,
            })
    return memories


def build(path=LEDGER, out=JSONL):
    memories = parse_ledger(path)
    with open(out, "w", encoding="utf-8") as f:
        for m in memories:
            f.write(json.dumps(m, ensure_ascii=False) + "\n")

    private = sum(1 for m in memories if m["sensitivity"] == "private")
    types = {}
    for m in memories:
        types[m["type"]] = types.get(m["type"], 0) + 1

    print(f"Parsed {len(memories)} memories from {path}")
    print(f"  public:  {len(memories) - private}")
    print(f"  private: {private}")
    print("  by type:")
    for t in sorted(types):
        print(f"    {t:<14} {types[t]}")
    print(f"Wrote {out}")
    return memories


def index(path=LEDGER, chroma_dir=CHROMA_DIR):
    """Embed each memory individually and store it in Chroma."""
    import chromadb
    import shutil

    memories = parse_ledger(path)
    if not memories:
        raise SystemExit("No memories parsed; refusing to index an empty ledger.")

    _, dp = _prefix_for(READER_MODEL)
    ef = make_embeddings(READER_MODEL, prefix=dp)

    ids = [m["id"] for m in memories]
    docs = [m["text"] for m in memories]
    metadatas = [
        {
            "id": m["id"],
            "type": m["type"],
            "sensitivity": m["sensitivity"],
            "flags": ",".join(m["flags"]),
            "section": m["section"],
            "source": os.path.basename(path),
        }
        for m in memories
    ]

    # One embedding per memory. No character chunker. The whole point.
    embeddings = ef(docs)

    shutil.rmtree(chroma_dir, ignore_errors=True)
    client = chromadb.PersistentClient(path=chroma_dir)
    col = client.get_or_create_collection("langchain", embedding_function=ef)
    col.add(ids=ids, documents=docs, metadatas=metadatas, embeddings=embeddings)

    print(f"Indexed {len(ids)} memories -> {chroma_dir}")
    print(f"  embedding model: {READER_MODEL}")
    return col


def query(question, k=5, chroma_dir=CHROMA_DIR, only_public=False):
    import chromadb

    if not os.path.exists(chroma_dir):
        raise SystemExit(f"No index at {chroma_dir}. Run 'index' first.")

    ef = make_embeddings(READER_MODEL)
    client = chromadb.PersistentClient(path=chroma_dir)
    col = client.get_collection("langchain", embedding_function=ef)

    where = {"sensitivity": "public"} if only_public else None
    res = col.query(
        query_texts=[question],
        n_results=k,
        where=where,
        include=["documents", "metadatas", "distances"],
    )

    results = []
    print(f"--- {k} closest memories to: {question!r} ---")
    for i, (doc, meta, dist) in enumerate(
        zip(res["documents"][0], res["metadatas"][0], res["distances"][0]), 1
    ):
        print(f"[{i}] distance={dist:.3f}  {meta.get('id')} "
              f"({meta.get('type')}/{meta.get('sensitivity')})")
        print(f"    {doc}")
        print()
        results.append((doc, meta, dist))
    return results


def show(memory_id=None, mtype=None, sensitivity=None, path=LEDGER):
    memories = parse_ledger(path)
    for m in memories:
        if memory_id and m["id"] != memory_id:
            continue
        if mtype and m["type"] != mtype:
            continue
        if sensitivity and m["sensitivity"] != sensitivity:
            continue
        flags = (" " + ",".join(m["flags"])) if m["flags"] else ""
        print(f"{m['id']} [{m['type']}|{m['sensitivity']}{flags}] {m['text']}")


def main():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)

    b = sub.add_parser("build", help="parse ledger -> JSONL")
    b.add_argument("--ledger", default=LEDGER)
    b.add_argument("--out", default=JSONL)

    i = sub.add_parser("index", help="embed every memory into the vector store")
    i.add_argument("--ledger", default=LEDGER)
    i.add_argument("--chroma-dir", default=CHROMA_DIR)

    q = sub.add_parser("query", help="retrieve closest memories")
    q.add_argument("question")
    q.add_argument("-k", type=int, default=5)
    q.add_argument("--chroma-dir", default=CHROMA_DIR)

    s = sub.add_parser("show", help="print memories")
    s.add_argument("--id")
    s.add_argument("--type")
    s.add_argument("--sensitivity")
    s.add_argument("--ledger", default=LEDGER)

    args = p.parse_args()

    if args.cmd == "build":
        build(args.ledger, args.out)
    elif args.cmd == "index":
        index(args.ledger, args.chroma_dir)
    elif args.cmd == "query":
        query(args.question, args.k, args.chroma_dir)
    elif args.cmd == "show":
        show(args.id, args.type, args.sensitivity, args.ledger)


if __name__ == "__main__":
    main()
