import json
import sqlite3
import faiss
import numpy as np
import os
from sentence_transformers import SentenceTransformer

# Paths to control corpus and database/index files
CONTROLS_JSON = "data/controls_nist.json"
SQLITE_DB = "data/controls.db"
FAISS_INDEX = "data/controls.faiss"
EMBED_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

class ControlIndex:
    def __init__(self, sqlite_path=SQLITE_DB, faiss_path=FAISS_INDEX, embed_model=EMBED_MODEL):
        # initialize SQLite
        self.conn = sqlite3.connect(sqlite_path)
        self._ensure_table()
        # initialize embedder
        self.embedder = SentenceTransformer(embed_model)
        # placeholders for FAISS index and id mapping
        self.index = None
        self.id_map = []
        self.faiss_path = faiss_path

    def _ensure_table(self):
        cursor = self.conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS controls (
                id TEXT PRIMARY KEY,
                title TEXT,
                text TEXT,
                family TEXT
            )
            """
        )
        self.conn.commit()

    def load_controls(self, json_path: str = CONTROLS_JSON):
        """
        Load controls from OSCAL JSON into SQLite if table is empty.
        """
        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM controls")
        count = cursor.fetchone()[0]
        if count > 0:
            return  # already loaded

        with open(json_path, 'r', encoding='utf-8') as f:
            catalog = json.load(f).get('catalog', {})
        # OSCAL structure: catalog -> groups -> controls
        controls = []
        for group in catalog.get('groups', []):
            for ctl in group.get('controls', []):
                cid = ctl.get('id')
                title = ctl.get('title', '')
                # combine all prose parts as text
                parts = ctl.get('parts', [])
                prose_texts = []
                for part in parts:
                    if 'prose' in part:
                        prose_texts.append(part['prose'])
                text = ' '.join(prose_texts)
                family = ctl.get('family', '')
                controls.append((cid, title, text, family))

        cursor.executemany(
            "INSERT OR IGNORE INTO controls (id, title, text, family) VALUES (?, ?, ?, ?)",
            controls
        )
        self.conn.commit()

    def build_faiss_index(self):
        """
        Embed all control texts and build a FAISS index, then save it to disk.
        """
        if os.path.exists(self.faiss_path):
            self.load_faiss()
            return

        cursor = self.conn.cursor()
        cursor.execute("SELECT id, text FROM controls ORDER BY id")
        rows = cursor.fetchall()
        if not rows:
            raise ValueError("No control text found to index.")

        ids, texts = zip(*rows)
        embeddings = self.embedder.encode(list(texts), convert_to_numpy=True)
        dim = embeddings.shape[1]

        index = faiss.IndexFlatL2(dim)
        index.add(embeddings)

        self.id_map = list(ids)
        self.index = index
        faiss.write_index(index, self.faiss_path)

    def load_faiss(self):
        """
        Load FAISS index from disk and rebuild id_map from SQLite.
        """
        self.index = faiss.read_index(self.faiss_path)
        cursor = self.conn.cursor()
        cursor.execute("SELECT id FROM controls ORDER BY id")
        self.id_map = [row[0] for row in cursor.fetchall()]

    def query(self, query_text: str, top_k: int = 5):
        """
        Return top_k controls most similar to query_text.
        Each result includes id, title, text, family, and similarity score.
        """
        if self.index is None:
            self.load_faiss()

        q_emb = self.embedder.encode([query_text], convert_to_numpy=True)
        distances, indices = self.index.search(q_emb, top_k)
        results = []
        cursor = self.conn.cursor()
        for dist, idx in zip(distances[0], indices[0]):
            cid = self.id_map[idx]
            cursor.execute(
                "SELECT title, text, family FROM controls WHERE id = ?", (cid,)
            )
            title, text, family = cursor.fetchone()
            results.append({
                'id': cid,
                'title': title,
                'text': text,
                'family': family,
                'score': float(dist)
            })
        return results
