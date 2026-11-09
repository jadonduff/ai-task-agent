import os, sqlite3, sqlite_vec
from functools import lru_cache
from sentence_transformers import SentenceTransformer
from sqlite_vec import serialize_float32

DB_PATH = os.environ.get("RAG_DB", "/app/rag/rag.db")
MODEL_NAME = os.environ["EMBED_MODEL"]
EMBED_DIM = int(os.environ.get("EMBED_DIM", "256"))
IDENT = f"{MODEL_NAME}@{EMBED_DIM}"

@lru_cache(maxsize=1)
def model() -> SentenceTransformer:
    m = SentenceTransformer(MODEL_NAME, truncate_dim=EMBED_DIM, device="cpu")
    print("embedding prompts:", m.prompts, flush=True)  # check these on first run
    return m

def embed_docs(texts):
    return model().encode_document(texts, batch_size=8, normalize_embeddings=True).tolist()

def embed_query(text):
    return model().encode_query(text, normalize_embeddings=True).tolist()

def connect():
    db = sqlite3.connect(DB_PATH)
    db.enable_load_extension(True)
    sqlite_vec.load(db)
    db.enable_load_extension(False)
    db.execute("CREATE TABLE IF NOT EXISTS chunks(id INTEGER PRIMARY KEY, source TEXT, idx INTEGER, text TEXT)")
    db.execute("CREATE TABLE IF NOT EXISTS meta(k TEXT PRIMARY KEY, v TEXT)")
    d = model().get_embedding_dimension()
    db.execute(f"CREATE VIRTUAL TABLE IF NOT EXISTS vec_chunks USING vec0(embedding float[{d}] distance_metric=cosine)")
    row = db.execute("SELECT v FROM meta WHERE k='model'").fetchone()
    if row and row[0] != IDENT:
        raise RuntimeError(f"Index built with {row[0]} but config is {IDENT}. Rebuild the image.")
    db.execute("INSERT OR REPLACE INTO meta VALUES('model', ?)", (IDENT,))
    db.commit()
    return db

def search(query: str, top_k: int = 5):
    db = connect()
    q = serialize_float32(embed_query(query))
    hits = db.execute(
        "SELECT rowid, distance FROM vec_chunks WHERE embedding MATCH ? AND k = ? ORDER BY distance",
        (q, top_k)).fetchall()
    out = []
    for rowid, dist in hits:
        src, idx, text = db.execute("SELECT source, idx, text FROM chunks WHERE id=?", (rowid,)).fetchone()
        out.append({"source": src, "chunk": idx, "score": round(1 - dist, 3), "text": text})
    db.close()
    return out