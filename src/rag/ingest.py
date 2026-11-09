import sys, pathlib
import pymupdf, docx
from .store import connect, embed_docs, serialize_float32

EXTS = {".md", ".txt", ".rst", ".pdf", ".docx"}

def read(path: pathlib.Path) -> str:
    ext = path.suffix.lower()
    if ext == ".pdf":
        with pymupdf.open(path) as d:
            return "\n\n".join(p.get_text() for p in d)
    if ext == ".docx":
        return "\n\n".join(p.text for p in docx.Document(str(path)).paragraphs)
    return path.read_text(errors="ignore")

def chunk(text, size=1500, overlap=200):
    """Pack paragraphs up to `size` chars; window-split oversized paragraphs."""
    out, cur = [], ""
    for p in (p.strip() for p in text.split("\n\n")):
        if not p:
            continue
        if len(cur) + len(p) + 2 <= size:
            cur = f"{cur}\n\n{p}" if cur else p
            continue
        if cur:
            out.append(cur)
        while len(p) > size:
            out.append(p[:size])
            p = p[size - overlap:]
        cur = p
    if cur:
        out.append(cur)
    return out

def main(root="/app/knowledge"):
    db = connect()
    db.execute("DELETE FROM vec_chunks")
    db.execute("DELETE FROM chunks")
    db.commit()
    root = pathlib.Path(root)
    files = [p for p in sorted(root.rglob("*")) if p.is_file() and p.suffix.lower() in EXTS]
    total = 0
    for path in files:
        src = str(path.relative_to(root))
        try:
            chunks = chunk(read(path))
        except Exception as e:
            print(f"skip {src}: {e}", flush=True)
            continue
        if not chunks:
            continue
        for n, (c, v) in enumerate(zip(chunks, embed_docs(chunks))):
            cur = db.execute("INSERT INTO chunks(source, idx, text) VALUES (?,?,?)", (src, n, c))
            db.execute("INSERT INTO vec_chunks(rowid, embedding) VALUES (?,?)",
                       (cur.lastrowid, serialize_float32(v)))
        db.commit()
        total += len(chunks)
        print(f"indexed {src}: {len(chunks)} chunks", flush=True)
    print(f"done: {len(files)} files, {total} chunks", flush=True)

if __name__ == "__main__":
    main(*sys.argv[1:])