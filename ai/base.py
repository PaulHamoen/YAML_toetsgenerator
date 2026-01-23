class AIClient:
    def generate_yaml(self, user_prompt: str) -> str:
        """
        Geeft een STRING terug met geldige YAML.
        Gooit een Exception bij fouten.
        """
        raise NotImplementedError

class BaseLLMClient:
    """
    Abstracte basis voor alle LLM-clients
    """

    def generate_yaml(self, prompt: str) -> str:
        raise NotImplementedError
