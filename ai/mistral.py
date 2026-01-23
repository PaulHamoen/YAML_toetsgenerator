import os
import requests
from ai.base import BaseLLMClient


class MistralClient(BaseLLMClient):
    def __init__(self, model="mistral-small"):
        self.api_key = os.getenv("MISTRAL_API_KEY")
        if not self.api_key:
            raise RuntimeError("MISTRAL_API_KEY ontbreekt. Zet deze in ai/.env")

        self.model = model
        self.endpoint = "https://api.mistral.ai/v1/chat/completions"

    def generate_yaml(self, prompt: str) -> str:
        system_prompt = (
            "Je bent een tool die ALLEEN geldige YAML produceert.\n"
            "Geen uitleg, geen tekst buiten YAML.\n"
            "De YAML moet exact voldoen aan deze structuur:\n\n"
            "toets:\n"
            "  opgaven:\n"
            "    - titel: string\n"
            "      delen:\n"
            "        - tekst: string\n"
            "          onderdelen:\n"
            "            - punten: int\n"
            "              mode: \"math\" | \"latex\"\n"
            "              inhoud: string\n"
        )

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
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
