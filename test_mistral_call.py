from ai.mistral import MistralClient

client = MistralClient()

prompt = (
    "Maak een korte wiskundetoets voor vwo 3 over herleiden "
    "met 1 opgave en 2 onderdelen."
)

yaml_output = client.generate_yaml(prompt)
print(yaml_output)
