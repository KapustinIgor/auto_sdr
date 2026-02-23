import json
from pathlib import Path

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

from app.services.llm import ollama_generate

MODEL = SentenceTransformer("all-MiniLM-L6-v2")


def build_faiss_index(account_id: int, snippets: list[str], index_dir: str = "data/faiss"):
    Path(index_dir).mkdir(parents=True, exist_ok=True)
    vectors = MODEL.encode(snippets)
    index = faiss.IndexFlatL2(vectors.shape[1])
    index.add(np.array(vectors).astype("float32"))
    faiss.write_index(index, f"{index_dir}/{account_id}.index")
    Path(f"{index_dir}/{account_id}.json").write_text(json.dumps(snippets))


def generate_brief(query: str, account_id: int, index_dir: str = "data/faiss"):
    index = faiss.read_index(f"{index_dir}/{account_id}.index")
    snippets = json.loads(Path(f"{index_dir}/{account_id}.json").read_text())
    qv = MODEL.encode([query]).astype("float32")
    _, idx = index.search(qv, 5)
    context = "\n".join(snippets[i] for i in idx[0] if i < len(snippets))
    prompt_template = Path("prompts/research_agent_v1.txt").read_text()
    prompt = prompt_template.format(context=context, query=query)
    return ollama_generate(prompt)
