# ai/ollama.py
import requests
from pathlib import Path

from ai.base import AIClient


class OllamaClient(AIClient):
    def __init__(self, model: str = "phi3:latest"):
        self.model = model
        self.url = "http://localhost:11434/api/chat"

        prompt_path = Path(__file__).parent / "prompt.txt"
        self.prompt_template = prompt_path.read_text(encoding="utf-8")

    def generate_yaml(self, user_prompt: str) -> str:
        prompt = self.prompt_template.replace(
            "{USER_PROMPT}", user_prompt.strip()
        )

        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "stream": False
        }

        try:
            r = requests.post(self.url, json=payload, timeout=600)
            r.raise_for_status()
        except Exception as e:
            raise RuntimeError(f"Ollama-fout: {e}")

        data = r.json()

        if "message" not in data or "content" not in data["message"]:
            raise RuntimeError("Ongeldige Ollama-respons")

        return data["message"]["content"].strip()
