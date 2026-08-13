from openai import OpenAI

client = OpenAI()

models = client.models.list()

for model in models.data:
    if "gpt" in model.id.lower():
        print(model.id)