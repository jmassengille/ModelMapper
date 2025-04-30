from typing import List, Tuple
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
import os
import nltk

from nltk.tokenize import sent_tokenize

nltk.download('punkt_tab')

try:
    import docx
except ImportError:
    docx = None

try:
    import PyPDF2
except ImportError:
    PyPDF2 = None

class EmbeddingPipeline:
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model = SentenceTransformer(model_name)
        self.index = None
        self.text_chunks = []

    def chunk_text(self, text: str, max_tokens: int = 200) -> List[str]:
        # Improved splitter using nltk sentence tokenizer
        sentences = sent_tokenize(text)
        chunks = []
        chunk = ""
        for sentence in sentences:
            if len(chunk) + len(sentence) < max_tokens:
                chunk += sentence + " "
            else:
                chunks.append(chunk.strip())
                chunk = sentence + " "
        if chunk:
            chunks.append(chunk.strip())
        return chunks

    def embed_chunks(self, chunks: List[str]) -> None:
        self.text_chunks = chunks
        vectors = self.model.encode(chunks, convert_to_numpy=True)
        self.index = faiss.IndexFlatL2(vectors.shape[1])
        self.index.add(vectors)

    def query(self, query_text: str, top_k: int = 5) -> List[Tuple[str, float]]:
        query_vec = self.model.encode([query_text], convert_to_numpy=True)
        distances, indices = self.index.search(query_vec, top_k)
        results = []
        for idx, dist in zip(indices[0], distances[0]):
            results.append((self.text_chunks[idx], dist))
        return results

    def process_uploaded_file(self, file_path: str):
        ext = os.path.splitext(file_path)[-1].lower()
        content = ""

        if ext == ".txt":
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

        elif ext == ".docx" and docx:
            doc = docx.Document(file_path)
            content = "\n".join([para.text for para in doc.paragraphs])

        elif ext == ".pdf" and PyPDF2:
            with open(file_path, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                content = "\n".join([page.extract_text() or "" for page in reader.pages])

        else:
            raise ValueError(f"Unsupported file type or missing parser: {ext}")

        chunks = self.chunk_text(content)
        self.embed_chunks(chunks)
        return len(chunks)
