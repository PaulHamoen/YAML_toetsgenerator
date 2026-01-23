import os
from ai.base import BaseLLMClient


class MistralClient(BaseLLMClient):
    def __init__(self, model="mistral-small"):
        self.api_key = os.getenv("MISTRAL_API_KEY")
        if not self.api_key:
            raise RuntimeError(
                "MISTRAL_API_KEY ontbreekt. Zet deze in ai/.env"
            )

        self.model = model

    def generate_yaml(self, prompt: str) -> str:
        raise NotImplementedError(
            "Mistral API-call nog niet geïmplementeerd"
        )
