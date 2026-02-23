import json
from pathlib import Path

from app.services.llm import ollama_generate


def generate_sequence(research_brief: dict):
    prompt = Path("prompts/copy_agent_v1.txt").read_text()
    proof_points = json.loads(Path("data/proof_points.json").read_text())
    final_prompt = prompt.format(research_brief=json.dumps(research_brief), proof_points=json.dumps(proof_points))
    return ollama_generate(final_prompt)
