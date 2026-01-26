import os
import requests
from pathlib import Path
from ai.base import BaseLLMClient


class MistralClient(BaseLLMClient):
    def __init__(self, model="mistral-small"):
        self.api_key = os.getenv("MISTRAL_API_KEY")
        if not self.api_key:
            raise RuntimeError("MISTRAL_API_KEY ontbreekt. Zet deze in ai/.env")

        self.model = model
        self.endpoint = "https://api.mistral.ai/v1/chat/completions"

        self.system_prompt = self._load_system_prompt()

    def _load_system_prompt(self) -> str:
        prompt_path = Path(__file__).resolve().parent / "prompt.txt"

        if not prompt_path.exists():
            raise RuntimeError(
                f"Systeemprompt ontbreekt: {prompt_path}"
            )

        content = prompt_path.read_text(encoding="utf-8").strip()

        if not content:
            raise RuntimeError("prompt.txt is leeg")

        return content

    def generate_yaml(self, prompt: str) -> str:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.2,
        }

        response = requests.post(
            self.endpoint,
            headers=headers,
            json=payload,
            timeout=30,
        )

        if response.status_code != 200:
            raise RuntimeError(
                f"Mistral API fout {response.status_code}: {response.text}"
            )

        data = response.json()

        try:
            content = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError):
            raise RuntimeError("Onverwachte Mistral-response structuur")

        return content.strip()
